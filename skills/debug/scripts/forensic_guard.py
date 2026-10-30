#!/usr/bin/env python3
"""
skills/debug/scripts/forensic_guard.py
Forensic Security Guardrail & Scratch Sanitizer for the `/debug` Skill.

Provides deterministic OWASP Top 10 for LLM & Agentic (2025/2026) mitigations:
1. --scan-mre <script_path>   : [DEBUG-ASI05-01] AST safety validation on probing/MRE scripts
                                before execution. Blocks `os.system`, `subprocess.*` with
                                `shell=True`, `shutil.rmtree`, `eval`, `exec`, and file writes
                                outside `.tmp/forensic-scratch/`.
2. --redact-trace <target>    : [DEBUG-LLM02-02] Redacts sensitive credentials, tokens, DSNs,
                                and PII in stack traces/logs before persisting to RCA reports
                                or Obsidian notes (`[REDACTED_SECRET]`).
3. --purge-scratch            : [DEBUG-ASI02-03] Safely removes temporary files inside
                                `.tmp/forensic-scratch/` and verifies via `git status --porcelain`
                                that no untracked probing scripts remain in the repository.
"""

import argparse
import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ALLOWED_SCRATCH_PREFIX = ".tmp/forensic-scratch"

# Regex patterns for secret and credential redaction [DEBUG-LLM02-02]
SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("BEARER_TOKEN", re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9\-._~+/]+=*")),
    ("OPENAI_KEY", re.compile(r"\bsk-(?:proj-|ant-|[A-Za-z0-9]{16,})[A-Za-z0-9\-_]*\b")),
    ("GOOGLE_API_KEY", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("GITHUB_TOKEN", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}\b")),
    ("AWS_ACCESS_KEY", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    (
        "DSN_PASSWORD",
        re.compile(r"((?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^:\s/]+:)([^@\s]+)(@)"),
    ),
    (
        "ENV_SECRET_ASSIGNMENT",
        re.compile(
            r"(?i)\b((?:api_?key|secret(?:_?key)?|password|passwd|access_?token|auth_?token|client_?secret)\s*[:=]\s*['\"]?)([^\s'\",;}{]+)(['\"]?)"
        ),
    ),
    ("EMAIL_PII", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
]


class MreSafetyVisitor(ast.NodeVisitor):
    """AST Visitor that enforces strict safety constraints on forensic probing/MRE scripts."""

    def __init__(self) -> None:
        self.violations: List[str] = []

    def _get_call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = self._get_call_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""

    def _extract_string_literal(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _is_path_outside_scratch(self, raw_path: str) -> bool:
        normalized = raw_path.replace("\\", "/").strip()
        if normalized in ("/dev/null", "nul", "NUL"):
            return False
        if normalized.startswith("./"):
            normalized = normalized[2:]
        return not normalized.startswith(ALLOWED_SCRATCH_PREFIX)

    def visit_Call(self, node: ast.Call) -> None:
        call_name = self._get_call_name(node.func)
        lineno = getattr(node, "lineno", 0)

        # 1. Block eval / exec / compile
        if call_name in ("eval", "exec", "compile", "builtins.eval", "builtins.exec"):
            self.violations.append(
                f"Line {lineno}: Forbidden dynamic code execution `{call_name}()` [DEBUG-ASI05-01]."
            )

        # 2. Block os.system / os.popen / os.remove / os.unlink / os.rmdir
        elif call_name in (
            "os.system",
            "os.popen",
            "os.spawnl",
            "os.spawnle",
            "os.spawnlp",
            "os.spawnlpe",
            "os.spawnv",
            "os.spawnve",
            "os.spawnvp",
            "os.spawnvpe",
            "posix.system",
            "nt.system",
        ):
            self.violations.append(
                f"Line {lineno}: Forbidden shell execution `{call_name}()` [DEBUG-ASI05-01]."
            )

        # 3. Block shutil.rmtree / shutil.move / shutil.copy* outside scratch
        elif call_name in ("shutil.rmtree", "rmtree"):
            self.violations.append(
                f"Line {lineno}: Forbidden recursive directory deletion `{call_name}()` [DEBUG-ASI05-01]."
            )

        # 4. Block subprocess.* with shell=True
        elif call_name.startswith("subprocess.") or call_name in (
            "Popen",
            "run",
            "call",
            "check_call",
            "check_output",
        ):
            for kw in node.keywords:
                if kw.arg == "shell":
                    if not (isinstance(kw.value, ast.Constant) and kw.value.value is False):
                        self.violations.append(
                            f"Line {lineno}: Forbidden `{call_name}(..., shell=True)` [DEBUG-ASI05-01]."
                        )

        # 5. Check file mutations outside .tmp/forensic-scratch/
        elif call_name in ("open", "io.open"):
            is_write = False
            if len(node.args) >= 2:
                mode_str = self._extract_string_literal(node.args[1])
                if mode_str and any(m in mode_str for m in ("w", "a", "x", "+")):
                    is_write = True
            for kw in node.keywords:
                if kw.arg == "mode":
                    mode_str = self._extract_string_literal(kw.value)
                    if mode_str and any(m in mode_str for m in ("w", "a", "x", "+")):
                        is_write = True

            if is_write and node.args:
                target_path = self._extract_string_literal(node.args[0])
                if target_path is None or self._is_path_outside_scratch(target_path):
                    self.violations.append(
                        f"Line {lineno}: File write via `open()` outside `{ALLOWED_SCRATCH_PREFIX}/` is forbidden [DEBUG-ASI05-01]."
                    )

        elif call_name.endswith((".write_text", ".write_bytes", ".unlink", ".rmdir")):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Call):
                inner_call = node.func.value
                inner_name = self._get_call_name(inner_call.func)
                if inner_name in ("Path", "pathlib.Path") and inner_call.args:
                    target_path = self._extract_string_literal(inner_call.args[0])
                    if target_path is None or self._is_path_outside_scratch(target_path):
                        self.violations.append(
                            f"Line {lineno}: Path mutation `{call_name}()` outside `{ALLOWED_SCRATCH_PREFIX}/` is forbidden [DEBUG-ASI05-01]."
                        )
            else:
                self.violations.append(
                    f"Line {lineno}: Unverified path mutation `{call_name}()` must explicitly target `{ALLOWED_SCRATCH_PREFIX}/` [DEBUG-ASI05-01]."
                )

        elif call_name in ("os.remove", "os.unlink", "os.rmdir", "os.replace", "os.rename"):
            if node.args:
                target_path = self._extract_string_literal(node.args[0])
                if target_path is None or self._is_path_outside_scratch(target_path):
                    self.violations.append(
                        f"Line {lineno}: File mutation `{call_name}()` outside `{ALLOWED_SCRATCH_PREFIX}/` is forbidden [DEBUG-ASI05-01]."
                    )

        self.generic_visit(node)


def scan_mre_script(script_path_str: str) -> Tuple[bool, List[str]]:
    """
    Validates that an MRE/probing script resides inside `.tmp/forensic-scratch/` (or is safe)
    and contains zero dangerous AST constructs.
    """
    path = Path(script_path_str)
    if not path.exists() or not path.is_file():
        return False, [f"MRE script not found: {script_path_str}"]

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return False, [f"Failed to read MRE script {script_path_str}: {exc}"]

    try:
        tree = ast.parse(source, filename=script_path_str)
    except SyntaxError as exc:
        return False, [f"Syntax error in MRE script {script_path_str} (line {exc.lineno}): {exc.msg}"]

    visitor = MreSafetyVisitor()
    visitor.visit(tree)

    return len(visitor.violations) == 0, visitor.violations


def redact_trace_text(raw_text: str) -> str:
    """Redacts sensitive tokens, API keys, DSN credentials, and PII from tracebacks or logs."""
    redacted = raw_text
    for name, pattern in SECRET_PATTERNS:
        if name == "BEARER_TOKEN":
            redacted = pattern.sub(r"\1[REDACTED_SECRET]", redacted)
        elif name == "DSN_PASSWORD":
            redacted = pattern.sub(r"\1[REDACTED_SECRET]\3", redacted)
        elif name == "ENV_SECRET_ASSIGNMENT":
            redacted = pattern.sub(r"\1[REDACTED_SECRET]\3", redacted)
        else:
            redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def purge_scratch_directory(repo_root: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Safely removes `.tmp/forensic-scratch/` and checks `git status --porcelain`
    to verify no untracked probing scripts (`reproduce_*.py`, `probe_*.py`) remain in the repo root.
    """
    base = repo_root or Path.cwd()
    scratch_dir = base / ".tmp" / "forensic-scratch"

    removed_count = 0
    if scratch_dir.exists() and scratch_dir.is_dir():
        for item in scratch_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            removed_count += 1
        try:
            scratch_dir.rmdir()
        except OSError:
            pass

    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(base),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except Exception as exc:
        return False, f"Failed to run `git status --porcelain`: {exc}"

    if proc.returncode != 0:
        return False, f"`git status --porcelain` failed with exit code {proc.returncode}: {proc.stderr.strip()}"

    leftover_probes: List[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        status_code = line[:2]
        file_path = line[3:].strip().strip('"').replace("\\", "/")
        if status_code == "??" and (
            file_path.startswith(".tmp/forensic-scratch")
            or re.search(r"(^|/)(reproduce_|probe_|mre_).*\.py$", file_path)
        ):
            leftover_probes.append(file_path)

    if leftover_probes:
        return (
            False,
            f"Untracked probing scripts remain in workspace: {', '.join(leftover_probes)}",
        )

    return True, f"Purged {removed_count} item(s) from `.tmp/forensic-scratch/`. Zero residual probing scripts."


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Forensic Guardrail CLI for `/debug` (AST MRE Scanner, Trace Redactor, Scratch Purger)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--scan-mre",
        metavar="SCRIPT_PATH",
        help="Run AST safety validation on a probing/MRE script before execution.",
    )
    group.add_argument(
        "--redact-trace",
        metavar="FILE_OR_TEXT",
        help="Redact sensitive credentials/tokens from a traceback file or inline string.",
    )
    group.add_argument(
        "--purge-scratch",
        action="store_true",
        help="Purge `.tmp/forensic-scratch/` and verify zero untracked probing scripts in repo.",
    )

    args = parser.parse_args(argv)

    if args.scan_mre:
        is_safe, violations = scan_mre_script(args.scan_mre)
        if not is_safe:
            print(f"[FORENSIC-GUARD BLOCKED] Unsafe MRE script: {args.scan_mre}", file=sys.stderr)
            for v in violations:
                print(f"  - {v}", file=sys.stderr)
            return 1
        print(f"[FORENSIC-GUARD OK] MRE script passed AST safety validation: {args.scan_mre}")
        return 0

    if args.redact_trace is not None:
        candidate_path = Path(args.redact_trace)
        if candidate_path.exists() and candidate_path.is_file():
            raw_content = candidate_path.read_text(encoding="utf-8", errors="replace")
        else:
            raw_content = args.redact_trace
        print(redact_trace_text(raw_content))
        return 0

    if args.purge_scratch:
        ok, msg = purge_scratch_directory()
        if not ok:
            print(f"[FORENSIC-GUARD ERROR] {msg}", file=sys.stderr)
            return 1
        print(f"[FORENSIC-GUARD OK] {msg}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
