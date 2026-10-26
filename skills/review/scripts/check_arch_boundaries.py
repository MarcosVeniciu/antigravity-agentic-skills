#!/usr/bin/env python3
"""
check_arch_boundaries.py - Architectural Layer Boundary Linter

Enforces Clean Architecture / Ports & Adapters boundary isolation.
Detects illegal infrastructure, framework, and UI imports within pure domain,
entity, and use case layers across Python (.py), TypeScript/JavaScript (.ts, .js), and Dart (.dart).
Part of the workflows-skill/review package.
"""

import sys
import os
import re
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class BoundaryRule:
    language: str
    extensions: Tuple[str, ...]
    forbidden_patterns: List[Tuple[re.Pattern, str]]  # (regex, description)


RULES: List[BoundaryRule] = [
    # Python Boundary Rules
    BoundaryRule(
        language="Python",
        extensions=(".py",),
        forbidden_patterns=[
            (
                re.compile(
                    r'^\s*(?:from\s+(?:sqlalchemy|flask|fastapi|django|boto3|requests|httpx|aiohttp|pymongo|redis)(?:\.[a-zA-Z0-9_]+)*\s+import|import\s+(?:sqlalchemy|flask|fastapi|django|boto3|requests|httpx|aiohttp|pymongo|redis)(?:\.[a-zA-Z0-9_]+)*\b)'
                ),
                "Domain layer must not import external database, HTTP client, or web framework packages."
            )
        ]
    ),
    # TypeScript / JavaScript Boundary Rules
    BoundaryRule(
        language="TypeScript/JavaScript",
        extensions=(".ts", ".tsx", ".js", ".jsx"),
        forbidden_patterns=[
            (
                re.compile(
                    r'^\s*(?:(?:import\s+.*?from\s+)|(?:const|let|var)\s+.*?=\s*require\s*\(\s*)["\'](axios|express|react|next|typeorm|prisma|@prisma(?:/[a-zA-Z0-9_\-]+)?|pg|mysql2?|redis|ioredis)(?:/[a-zA-Z0-9_\-\./]*)?["\']'
                ),
                "Domain layer must not import ORM, HTTP client, React, or server framework modules."
            )
        ]
    ),
    # Dart / Flutter Boundary Rules
    BoundaryRule(
        language="Dart/Flutter",
        extensions=(".dart",),
        forbidden_patterns=[
            (
                re.compile(r'^\s*import\s+["\']package:flutter/'),
                "Pure domain/entity/use-case must not depend on Flutter UI framework."
            ),
            (
                re.compile(r'^\s*import\s+["\'](?:dart:io|package:http/|package:dio/|package:shared_preferences/|package:sqflite/)'),
                "Pure domain layer must not depend directly on concrete I/O, HTTP, or persistence drivers."
            )
        ]
    )
]

DOMAIN_DIR_SEGMENTS = {
    "domain", "entities", "entity", "use_cases", "usecases", "usecase"
}


def is_domain_file(path: Path) -> bool:
    """
    Checks if a file resides inside a domain directory boundary.
    Uses directory path segments rather than raw substring matching to avoid false positives.
    """
    parts = [part.lower() for part in path.parts]
    for part in parts[:-1]:
        if part in DOMAIN_DIR_SEGMENTS:
            return True
        if part == "core" and "domain" in parts:
            return True
    return False


@dataclass
class BoundaryViolation:
    file_path: str
    line_number: int
    matched_import: str
    reason: str


def check_file(file_path: Path, force_check: bool = False) -> Tuple[List[BoundaryViolation], Optional[str]]:
    violations: List[BoundaryViolation] = []
    
    if not force_check and not is_domain_file(file_path):
        return violations, None

    ext = file_path.suffix.lower()
    applicable_rules = [r for r in RULES if ext in r.extensions]
    if not applicable_rules:
        return violations, None

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return violations, f"Could not read {file_path}: {e}"

    for rule in applicable_rules:
        for idx, line in enumerate(lines, start=1):
            for pattern, reason in rule.forbidden_patterns:
                if pattern.search(line):
                    violations.append(BoundaryViolation(
                        file_path=str(file_path),
                        line_number=idx,
                        matched_import=line.strip(),
                        reason=reason
                    ))
    return violations, None


def print_report(
    violations: List[BoundaryViolation],
    domain_files_scanned: int,
    total_files_examined: int,
    files_with_errors: List[Tuple[str, str]],
    files_not_found: List[str]
) -> int:
    print(f"\n{'='*80}")
    print("🏛️  ARCHITECTURAL LAYER BOUNDARY AUDIT REPORT")
    print(f"{'='*80}")
    print(f"Total files examined:   {total_files_examined}")
    print(f"Domain files inspected: {domain_files_scanned}")
    print(f"Boundary violations:    {len(violations)}")
    if files_with_errors:
        print(f"Files with read errors: {len(files_with_errors)}")
    if files_not_found:
        print(f"Targets not found:      {len(files_not_found)}")
    print()

    if files_not_found:
        print("⚠️  MISSING TARGETS:")
        for nf in files_not_found:
            print(f"   [!] Target does not exist: {nf}")
        print()

    if files_with_errors:
        print("⚠️  FILE READ ERRORS:")
        for fp, err in files_with_errors:
            print(f"   [!] {fp}: {err}")
        print()

    if not violations and not files_with_errors and not files_not_found:
        if domain_files_scanned == 0:
            print("ℹ️  [INFO] No domain files identified among the provided targets.")
            print("    (Use --force-all if you wish to verify boundary rules on all target files regardless of path).")
        else:
            print("✅ [PASS] All scanned domain layers respect architectural boundary isolation.")
        print(f"{'='*80}\n")
        return 0

    if not violations and (files_with_errors or files_not_found):
        print("⚠️ [INCOMPLETE] No violations in readable domain files, but some targets could not be verified.")
        print(f"{'='*80}\n")
        return 1

    print("-" * 80)
    for v in violations:
        print(f"🔴 [VIOLATION] Architectural Leakage in Domain Layer")
        print(f"   📍 Location: {v.file_path}:{v.line_number}")
        print(f"   🔎 Import:   {v.matched_import}")
        print(f"   ⚠️ Reason:   {v.reason}")
        print(f"   💡 Fix:      Invert dependency: declare a domain Interface/Port and inject concrete Adapter via DI.")
        print("-" * 80)

    print(f"{'='*80}\n")
    return 1


def main():
    parser = argparse.ArgumentParser(
        description="Architectural Boundary Linter for Domain and Entity Isolation"
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help="Files or directories to scan (checks domain/entities/use_cases layers)"
    )
    parser.add_argument(
        "--force-all",
        action="store_true",
        help="Treat all specified files as domain files regardless of folder name"
    )
    parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit with code 0 (warning mode)"
    )

    args = parser.parse_args()

    files: List[Path] = []
    files_not_found: List[str] = []

    for t in args.targets:
        p = Path(t)
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for ext in (".py", ".ts", ".js", ".tsx", ".jsx", ".dart"):
                files.extend(p.glob(f"**/*{ext}"))
        else:
            files_not_found.append(t)

    violations: List[BoundaryViolation] = []
    files_with_errors: List[Tuple[str, str]] = []
    scanned_domain_count = 0

    for f in files:
        is_target_domain = args.force_all or is_domain_file(f)
        if is_target_domain:
            scanned_domain_count += 1
            f_violations, err = check_file(f, force_check=args.force_all)
            if err:
                files_with_errors.append((str(f), err))
            violations.extend(f_violations)

    exit_code = print_report(
        violations,
        scanned_domain_count,
        len(files),
        files_with_errors,
        files_not_found
    )
    
    if args.exit_zero:
        sys.exit(0)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
