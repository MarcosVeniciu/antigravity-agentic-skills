#!/usr/bin/env python3
"""
workflows-skill/infra/scripts/validate_env.py
Cross-platform Environment and Secret Containment Validator.
Converted from legacy skills/infra/scripts/validate_env.sh to Multiplatform Python CLI.

Enforces:
1. Syntax validity of KEY=VALUE pairs in .env and .env.example files.
2. Quoting rules for values containing spaces or special characters.
3. Secret containment heuristics (detects exposed AWS keys, JWTs, OpenAI keys, RSA/SSH private keys).
4. Parity and completeness between .env and .env.example (flags missing variables).
5. Warning detection for empty variables in template files.
6. Multiplatform UTF-8 console stream safety on Windows (cp1252 fix).
"""

import sys
import os
import re
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Set, Optional

# Fix Windows cp1252 console crash when printing unicode emojis/symbols
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Key syntax: Must start with a letter or underscore, followed by letters, digits, or underscores
KEY_REGEX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Security Heuristics (matches legacy validate_env.sh rules + modern token patterns)
SECURITY_PATTERNS = [
    (
        "AWS Access Key",
        re.compile(r"AKIA[0-9A-Z]{16}"),
        "CRITICAL: Leaked AWS Access Key ID detected.",
    ),
    (
        "JSON Web Token (JWT)",
        re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}"),
        "CRITICAL: Possible real signed JWT detected.",
    ),
    (
        "OpenAI API Key",
        re.compile(r"sk-[a-zA-Z0-9]{32,}|sk-proj-[a-zA-Z0-9_-]{32,}"),
        "CRITICAL: Possible live OpenAI API key detected.",
    ),
    (
        "Private Key",
        re.compile(r"-----BEGIN[ A-Z_-]*PRIVATE KEY"),
        "CRITICAL: Cryptographic Private Key block detected.",
    ),
    (
        "GitHub Token",
        re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}|github_pat_[A-Za-z0-9_]{40,}"),
        "CRITICAL: Possible live GitHub personal access or OAuth token detected.",
    ),
]


class EnvFileValidator:
    def __init__(self, file_path: Path, is_example: bool = False, strict: bool = False):
        self.file_path = file_path
        self.is_example = is_example or (".example" in file_path.name.lower())
        self.strict = strict
        self.parsed_vars: Dict[str, str] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        if not self.file_path.exists():
            self.errors.append(f"File '{self.file_path}' does not exist.")
            return False

        try:
            content = self.file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self.errors.append(f"Failed to read '{self.file_path}': {e}")
            return False

        lines = content.splitlines()
        for line_num, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            # Ignore empty lines and comment lines
            if not line or line.startswith("#"):
                continue

            # Basic KEY=VALUE syntax check
            if "=" not in line:
                self.errors.append(
                    f"[Line {line_num}] Syntax error: Missing '=' in '{raw_line}'"
                )
                continue

            key_part, val_part = line.split("=", 1)
            clean_key = key_part.strip()

            if not KEY_REGEX.match(clean_key):
                self.errors.append(
                    f"[Line {line_num}] Invalid key identifier '{clean_key}'. "
                    f"Must start with a letter/underscore and contain only alphanumeric characters or underscores."
                )
                continue

            raw_val = val_part.strip()

            # Quoting check: determine if value is quoted
            is_double_quoted = raw_val.startswith('"') and raw_val.endswith('"') and len(raw_val) >= 2
            is_single_quoted = raw_val.startswith("'") and raw_val.endswith("'") and len(raw_val) >= 2
            is_quoted = is_double_quoted or is_single_quoted

            # Extract unquoted value
            if is_quoted:
                unquoted_val = raw_val[1:-1]
            else:
                unquoted_val = raw_val

            # Detect unquoted spaces in value
            if not is_quoted and any(ch.isspace() for ch in raw_val):
                self.errors.append(
                    f"[Line {line_num}] Unquoted whitespace in '{clean_key}'. "
                    f"Values containing spaces must be enclosed in quotes: {clean_key}=\"{raw_val}\""
                )

            # Detect empty values in template files
            if self.is_example and not unquoted_val:
                self.warnings.append(
                    f"[Line {line_num}] Variable '{clean_key}' has an empty value. "
                    f"Consider adding a descriptive placeholder."
                )

            # Security heuristics: scan for leaked credentials
            for pattern_name, regex, desc in SECURITY_PATTERNS:
                # Exclude explicit placeholder values from false positives
                lower_val = unquoted_val.lower()
                if "placeholder" in lower_val or "your-super-secret" in lower_val or "example" in lower_val:
                    continue

                if regex.search(unquoted_val):
                    self.errors.append(
                        f"[Line {line_num}] Security Alert: Exposed {pattern_name} in '{clean_key}'! {desc}"
                    )

            self.parsed_vars[clean_key] = unquoted_val

        if self.strict and self.warnings:
            self.errors.extend([f"Strict Mode Warning as Error: {w}" for w in self.warnings])

        return len(self.errors) == 0


def compare_env_against_example(
    env_keys: Set[str],
    example_keys: Set[str],
    env_name: str = ".env",
    example_name: str = ".env.example",
) -> Tuple[List[str], List[str]]:
    """Compares variables declared in .env against .env.example."""
    missing_in_env = example_keys - env_keys
    missing_in_example = env_keys - example_keys

    errors: List[str] = []
    warnings: List[str] = []

    if missing_in_env:
        errors.append(
            f"Missing required variables in '{env_name}' that are declared in '{example_name}':\n"
            + "\n".join(f"    - {k}" for k in sorted(missing_in_env))
        )

    if missing_in_example:
        warnings.append(
            f"Variables present in '{env_name}' but missing documentation in '{example_name}':\n"
            + "\n".join(f"    - {k}" for k in sorted(missing_in_example))
            + f"\n    Action: Document these in '{example_name}' with safe placeholders."
        )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cross-platform Environment and Secret Containment Validator."
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Optional primary file to validate (default: '.env.example' or '.env').",
    )
    parser.add_argument(
        "--env",
        dest="env_file",
        default=None,
        help="Path to active local .env file to validate.",
    )
    parser.add_argument(
        "--example",
        dest="example_file",
        default=None,
        help="Path to .env.example reference file.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (returns exit code 1).",
    )

    args = parser.parse_args()

    # Determine validation mode
    if args.env_file and args.example_file:
        primary_env = Path(args.env_file)
        example_env = Path(args.example_file)
    elif args.file:
        primary_path = Path(args.file)
        if ".example" in primary_path.name.lower():
            primary_env = None
            example_env = primary_path
        else:
            primary_env = primary_path
            example_env = None
    else:
        # Default fallback
        default_example = Path(".env.example")
        default_env = Path(".env")
        if default_example.exists() and default_env.exists():
            primary_env = default_env
            example_env = default_example
        elif default_example.exists():
            primary_env = None
            example_env = default_example
        else:
            primary_env = default_env
            example_env = None

    total_errors: List[str] = []
    total_warnings: List[str] = []

    # Validate .env.example if present
    example_keys: Set[str] = set()
    if example_env:
        print(f"🔍 Validating template file: '{example_env}'...")
        val_example = EnvFileValidator(example_env, is_example=True, strict=args.strict)
        val_example.validate()
        example_keys = set(val_example.parsed_vars.keys())
        total_errors.extend([f"[{example_env.name}] {e}" for e in val_example.errors])
        total_warnings.extend([f"[{example_env.name}] {w}" for w in val_example.warnings])

    # Validate .env if present
    env_keys: Set[str] = set()
    if primary_env:
        print(f"🔍 Validating environment file: '{primary_env}'...")
        val_env = EnvFileValidator(primary_env, is_example=False, strict=args.strict)
        val_env.validate()
        env_keys = set(val_env.parsed_vars.keys())
        total_errors.extend([f"[{primary_env.name}] {e}" for e in val_env.errors])
        total_warnings.extend([f"[{primary_env.name}] {w}" for w in val_env.warnings])

    # Parity comparison if both files are specified
    if primary_env and example_env and primary_env.exists() and example_env.exists():
        print(f"⚖️ Comparing '{primary_env.name}' against '{example_env.name}'...")
        comp_errors, comp_warnings = compare_env_against_example(
            env_keys, example_keys, primary_env.name, example_env.name
        )
        total_errors.extend(comp_errors)
        total_warnings.extend(comp_warnings)

    print("----------------------------------------------------------------------")
    if total_warnings:
        print(f"⚠️ {len(total_warnings)} Warning(s) detected:")
        for w in total_warnings:
            print(f"   {w}")

    if total_errors:
        print(f"❌ Validation FAILED! {len(total_errors)} Error(s) detected:")
        for err in total_errors:
            print(f"   {err}")
        return 1

    if total_warnings and args.strict:
        print("❌ Strict mode enabled: Failing due to warnings.")
        return 1

    print("✅ Environment validation COMPLETED SUCCESSFULLY! No syntax or security issues detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
