#!/usr/bin/env python3
"""
skills/obsidian/scripts/validate_vault_note.py
Deterministic Obsidian Vault Note Validator (Schema, Memory Poisoning & Wikilink Parity).

Enforces OWASP LLM & Agentic (2025/2026) mitigations:
1. [OBS-LLM10-03] YAML Frontmatter Schema Validation:
   - Verifies note starts and ends frontmatter cleanly with '---'.
   - Parses via yaml.safe_load as a dict.
   - Validates required keys: type, feature, project ('antigravity'), date ('YYYY-MM-DD'),
     description, tags (non-empty list).
   - Validates 'type' against {'adr', 'domain_rule', 'pivot', 'sdd', 'bdd', 'dod', 'audit', 'changelog', 'epic'}.
   - Validates optional 'status' against {'proposed', 'accepted', 'superseded', 'deprecated', 'verified', 'active', 'completed'}.
2. [OBS-ASI06-01] Prompt Injection & Memory Poisoning Scanner:
   - Scans note content for adversarial directives attempting to poison persistent Vault memory.
   - Flags violations as [MEMORY_POISONING_RISK] and exits with code 1.
3. [OBS-ASI08-05] Wikilink Referential Integrity:
   - When --vault-root <dir> is provided, extracts all [[wikilinks]] outside fenced code blocks
     (stripping #heading and |alias) and verifies that each target .md file exists on disk.
"""

import argparse
import datetime
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

# Fix Windows cp1252 console encoding issues
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ALLOWED_TYPES: Set[str] = {
    "adr",
    "domain_rule",
    "pivot",
    "sdd",
    "bdd",
    "dod",
    "audit",
    "changelog",
    "epic",
}

ALLOWED_STATUSES: Set[str] = {
    "proposed",
    "accepted",
    "superseded",
    "deprecated",
    "verified",
    "active",
    "completed",
}

REQUIRED_KEYS: Tuple[str, ...] = (
    "type",
    "feature",
    "project",
    "date",
    "description",
    "tags",
)

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# [OBS-ASI06-01] Adversarial patterns targeting persistent Vault memory poisoning
MEMORY_POISONING_PATTERNS: List[Tuple[str, re.Pattern]] = [
    (
        "Ignore Previous Instructions",
        re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+(?:instructions|rules|prompts|directives)", re.IGNORECASE),
    ),
    (
        "System Override Directive",
        re.compile(r"system\s+override\s*:", re.IGNORECASE),
    ),
    (
        "Disregard Security Guardrail",
        re.compile(r"disregard\s+(?:all\s+)?security", re.IGNORECASE),
    ),
    (
        "Bypass SDD Drift Gate",
        re.compile(r"bypass\s+check_sdd_drift", re.IGNORECASE),
    ),
    (
        "Force Exit Zero Flag Manipulation",
        re.compile(r"--exit-zero\b", re.IGNORECASE),
    ),
    (
        "Embedded Script Tag Injection",
        re.compile(r"<\s*script\b[^>]*>", re.IGNORECASE),
    ),
]


def extract_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str, List[str]]:
    """
    Extracts and parses YAML frontmatter delimited by '---' at the start of the note.
    Returns (parsed_dict_or_None, body_text, error_messages).
    """
    errors: List[str] = []
    if not content.startswith("---"):
        errors.append("[SCHEMA_ERROR] Note must start with YAML frontmatter delimiter '---' on line 1.")
        return None, content, errors

    match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n(.*))?$", content, re.DOTALL)
    if not match:
        errors.append("[SCHEMA_ERROR] Unclosed or malformed YAML frontmatter delimiter '---'.")
        return None, content, errors

    raw_yaml = match.group(1)
    body = match.group(2) or ""

    try:
        parsed = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as exc:
        errors.append(f"[SCHEMA_ERROR] Invalid YAML syntax in frontmatter: {exc}")
        return None, body, errors

    if not isinstance(parsed, dict):
        errors.append("[SCHEMA_ERROR] YAML frontmatter must parse as a key-value mapping (dict).")
        return None, body, errors

    return parsed, body, errors


def validate_frontmatter_schema(frontmatter: Dict[str, Any]) -> List[str]:
    """Validates required keys, types, date format, and allowed enums ([OBS-LLM10-03])."""
    errors: List[str] = []

    for key in REQUIRED_KEYS:
        if key not in frontmatter or frontmatter[key] is None:
            errors.append(f"[SCHEMA_ERROR] Missing required frontmatter key: '{key}'.")

    if errors:
        return errors

    # 1. Validate 'type'
    note_type = frontmatter.get("type")
    if not isinstance(note_type, str) or note_type not in ALLOWED_TYPES:
        errors.append(
            f"[SCHEMA_ERROR] Invalid frontmatter 'type': '{note_type}'. "
            f"Allowed values: {sorted(ALLOWED_TYPES)}."
        )

    # 2. Validate 'feature'
    feature = frontmatter.get("feature")
    if not isinstance(feature, str) or not feature.strip():
        errors.append("[SCHEMA_ERROR] Frontmatter 'feature' must be a non-empty string.")

    # 3. Validate 'project'
    project = frontmatter.get("project")
    if project != "antigravity":
        errors.append(
            f"[SCHEMA_ERROR] Frontmatter 'project' must be 'antigravity' (got '{project}')."
        )

    # 4. Validate 'date' (YYYY-MM-DD string or datetime.date loaded by PyYAML)
    raw_date = frontmatter.get("date")
    if isinstance(raw_date, datetime.date) and not isinstance(raw_date, datetime.datetime):
        date_str = raw_date.strftime("%Y-%m-%d")
    elif isinstance(raw_date, str):
        date_str = raw_date.strip()
    else:
        date_str = ""

    if not DATE_REGEX.match(date_str):
        errors.append(
            f"[SCHEMA_ERROR] Frontmatter 'date' must follow 'YYYY-MM-DD' format (got '{raw_date}')."
        )
    else:
        try:
            datetime.date.fromisoformat(date_str)
        except ValueError as exc:
            errors.append(f"[SCHEMA_ERROR] Invalid calendar date in 'date': '{raw_date}' ({exc}).")

    # 5. Validate 'description'
    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("[SCHEMA_ERROR] Frontmatter 'description' must be a non-empty string.")

    # 6. Validate 'tags'
    tags = frontmatter.get("tags")
    if not isinstance(tags, list) or len(tags) == 0:
        errors.append("[SCHEMA_ERROR] Frontmatter 'tags' must be a non-empty list.")
    elif not all(isinstance(t, str) and t.strip() for t in tags):
        errors.append("[SCHEMA_ERROR] All elements in 'tags' must be non-empty strings.")

    # 7. Validate optional 'status'
    if "status" in frontmatter and frontmatter["status"] is not None:
        status_val = frontmatter["status"]
        if not isinstance(status_val, str) or status_val not in ALLOWED_STATUSES:
            errors.append(
                f"[SCHEMA_ERROR] Invalid frontmatter 'status': '{status_val}'. "
                f"Allowed values: {sorted(ALLOWED_STATUSES)}."
            )

    return errors


def scan_memory_poisoning(content: str) -> List[str]:
    """
    Scans note content for adversarial prompt injection directives ([OBS-ASI06-01]).
    Returns a list of formatted [MEMORY_POISONING_RISK] error messages.
    """
    errors: List[str] = []
    for line_num, line in enumerate(content.splitlines(), start=1):
        for rule_name, pattern in MEMORY_POISONING_PATTERNS:
            match = pattern.search(line)
            if match:
                errors.append(
                    f"[MEMORY_POISONING_RISK] Line {line_num}: Detected '{rule_name}' "
                    f"pattern ('{match.group(0)}') attempting to poison persistent Vault memory."
                )
    return errors


def strip_fenced_code_blocks(text: str) -> str:
    """Removes fenced code blocks (```...```) so wikilinks inside code examples are ignored."""
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def extract_wikilinks(content: str) -> List[str]:
    """
    Extracts all [[wikilinks]] outside fenced code blocks, stripping #heading and |alias.
    """
    cleaned = strip_fenced_code_blocks(content)
    raw_matches = re.findall(r"\[\[([^\[\]]+)\]\]", cleaned)
    targets: List[str] = []
    for raw in raw_matches:
        target = raw.split("|", 1)[0].split("#", 1)[0].strip()
        if target:
            targets.append(target)
    return targets


def validate_wikilinks(content: str, vault_root: Path) -> List[str]:
    """
    Verifies that every [[wikilink]] resolves to an existing .md file within vault_root ([OBS-ASI08-05]).
    """
    errors: List[str] = []
    if not vault_root.exists() or not vault_root.is_dir():
        errors.append(f"[WIKILINK_ERROR] Vault root directory does not exist: '{vault_root}'.")
        return errors

    targets = extract_wikilinks(content)
    if not targets:
        return errors

    # Index all markdown files in vault_root by stem and by relative path (with and without .md)
    md_files = list(vault_root.rglob("*.md"))
    known_stems: Set[str] = set()
    known_rel_paths: Set[str] = set()

    for md_file in md_files:
        known_stems.add(md_file.stem)
        rel_posix = md_file.relative_to(vault_root).as_posix()
        known_rel_paths.add(rel_posix)
        if rel_posix.endswith(".md"):
            known_rel_paths.add(rel_posix[:-3])

    for target in targets:
        norm_target = target.replace("\\", "/").lstrip("/")
        if norm_target.endswith(".md"):
            norm_no_ext = norm_target[:-3]
        else:
            norm_no_ext = norm_target

        exists = (
            norm_target in known_rel_paths
            or norm_no_ext in known_rel_paths
            or norm_no_ext in known_stems
        )
        if not exists:
            errors.append(
                f"[WIKILINK_ERROR] Broken wikilink '[[{target}]]': target '.md' note not found in vault '{vault_root}'."
            )

    return errors


def validate_note_file(note_path: Path, vault_root: Optional[Path] = None) -> List[str]:
    """Runs all deterministic validations on a single Obsidian markdown note."""
    errors: List[str] = []
    if not note_path.exists():
        return [f"[FILE_ERROR] Note file does not exist: '{note_path}'."]

    try:
        content = note_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [f"[FILE_ERROR] Failed to read '{note_path}': {exc}"]

    # 1. Frontmatter extraction & schema check
    frontmatter, _body, fm_errors = extract_frontmatter(content)
    errors.extend(fm_errors)
    if frontmatter is not None:
        errors.extend(validate_frontmatter_schema(frontmatter))

    # 2. Adversarial memory poisoning scan
    errors.extend(scan_memory_poisoning(content))

    # 3. Wikilink referential integrity check (when --vault-root is provided)
    if vault_root is not None:
        errors.extend(validate_wikilinks(content, vault_root))

    return errors


def collect_target_notes(target_path: Path) -> List[Path]:
    """Returns a sorted list of .md files from a file path or directory."""
    if target_path.is_file():
        return [target_path]
    if target_path.is_dir():
        return sorted(
            p for p in target_path.rglob("*.md")
            if not any(part.startswith(".") for part in p.relative_to(target_path).parts)
        )
    return []


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic Obsidian Vault Note Validator (YAML Schema, Memory Poisoning & Wikilinks)."
    )
    parser.add_argument(
        "target",
        help="Path to a single Obsidian note (.md) or a directory of notes to validate.",
    )
    parser.add_argument(
        "--vault-root",
        dest="vault_root",
        default=None,
        help="Optional root directory of the Obsidian Vault to verify [[wikilink]] referential integrity.",
    )

    args = parser.parse_args()
    target_path = Path(args.target)
    vault_root = Path(args.vault_root) if args.vault_root else None

    if not target_path.exists():
        print(f"❌ [FILE_ERROR] Target path does not exist: '{target_path}'")
        return 1

    notes = collect_target_notes(target_path)
    if not notes:
        print(f"❌ [FILE_ERROR] No markdown (.md) files found at: '{target_path}'")
        return 1

    total_errors: List[str] = []
    for note in notes:
        note_errors = validate_note_file(note, vault_root=vault_root)
        for err in note_errors:
            total_errors.append(f"[{note.name}] {err}")

    if total_errors:
        print(f"❌ Vault Note Validation FAILED ({len(total_errors)} violation(s) in {len(notes)} file(s)):")
        for err in total_errors:
            print(f"  - {err}")
        return 1

    print(f"✅ Vault Note Validation PASSED ({len(notes)} file(s) verified).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
