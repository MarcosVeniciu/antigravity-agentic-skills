#!/usr/bin/env python3
"""
lint_onboarding_commands.py - Onboarding Shell Command & Supply Chain Linter

Part of the /docs skill in SDD 2.0 (EV-DOC-03, [DOC-LLM04-04], [DOC-ASI04]).
Audits shell code blocks (bash/sh/shell) in README.md files to prevent supply chain poisoning
and unauthenticated command execution from leaking into onboarding guides.

Enforces:
1. Strict allowlist of approved package managers and build tools:
   {"pip", "pip3", "poetry", "uv", "python", "python3", "pytest",
    "npm", "pnpm", "yarn", "cargo", "docker", "docker-compose",
    "git", "make", "dotnet", "go", "cd"}
2. Zero unauthenticated downloaders (curl, wget).
3. Zero piping to interpreters (| sh, | bash, | python, etc.).
4. Zero command substitution (`cmd`, $(cmd)).
"""

import argparse
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_ALLOWED_COMMANDS: Set[str] = {
    "pip",
    "pip3",
    "poetry",
    "uv",
    "python",
    "python3",
    "pytest",
    "npm",
    "pnpm",
    "yarn",
    "cargo",
    "docker",
    "docker-compose",
    "git",
    "make",
    "dotnet",
    "go",
    "cd",
}

FORBIDDEN_DOWNLOADERS = re.compile(r"\b(curl|wget)\b", re.IGNORECASE)
FORBIDDEN_INTERPRETER_PIPE = re.compile(
    r"\|\s*(?:(?:/usr/bin/|/bin/)?(?:sh|bash|zsh|dash|python|python3|perl|ruby|node))\b",
    re.IGNORECASE,
)
COMMAND_SUBSTITUTION_BACKTICKS = re.compile(r"`[^`]+`")
COMMAND_SUBSTITUTION_DOLLAR = re.compile(r"\$\([^)]+\)")


@dataclass
class LintViolation:
    file_path: str
    line_number: int
    command_snippet: str
    reason: str


def extract_shell_blocks(content: str) -> List[Tuple[int, List[Tuple[int, str]]]]:
    """
    Extracts fenced shell code blocks (```bash, ```sh, ```shell, ```zsh) from markdown content.
    Returns:
        List of (block_start_line, [(line_no, line_text), ...])
    """
    blocks = []
    lines = content.splitlines()
    in_block = False
    current_lines = []
    block_start = 0

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if not in_block:
            if stripped.startswith("```"):
                tag = stripped[3:].strip().lower()
                if tag in ("bash", "sh", "shell", "zsh"):
                    in_block = True
                    block_start = idx
                    current_lines = []
        else:
            if stripped.startswith("```"):
                in_block = False
                blocks.append((block_start, current_lines))
                current_lines = []
            else:
                current_lines.append((idx, line))

    return blocks


def parse_logical_commands(
    block_lines: List[Tuple[int, str]]
) -> List[Tuple[int, str]]:
    """
    Assembles physical lines into logical command lines, handling trailing backslash continuations.
    """
    logical = []
    accumulated = ""
    start_line = 0

    for line_no, line in block_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not accumulated:
            start_line = line_no

        if stripped.endswith("\\"):
            accumulated += stripped[:-1] + " "
        else:
            accumulated += stripped
            logical.append((start_line, accumulated.strip()))
            accumulated = ""

    if accumulated:
        logical.append((start_line, accumulated.strip()))

    return logical


def split_subcommands(command_line: str) -> List[List[str]]:
    """
    Splits a logical command line by shell operators (&&, ||, ;, |) using shlex.
    """
    try:
        tokens = shlex.split(command_line, comments=True)
    except Exception:
        # Fallback split on whitespace if quoting is irregular
        tokens = command_line.split()

    subcommands = []
    current = []
    for token in tokens:
        if token in ("&&", "||", ";", "|"):
            if current:
                subcommands.append(current)
                current = []
        else:
            current.append(token)
    if current:
        subcommands.append(current)

    return subcommands


def extract_executable_name(tokens: List[str]) -> Optional[str]:
    """
    Extracts the executable name from tokens, skipping leading environment variable assignments.
    """
    for token in tokens:
        # Skip environment assignments like KEY=VALUE
        if "=" in token and not token.startswith("-"):
            continue
        # Extract base executable name
        return Path(token).name.lower()
    return None


def lint_markdown_content(
    content: str, file_path: str = "README.md", extra_allowed: Optional[Set[str]] = None
) -> List[LintViolation]:
    """
    Lints markdown content for unsafe shell commands and supply chain poisoning vectors.
    """
    allowed_commands = set(DEFAULT_ALLOWED_COMMANDS)
    if extra_allowed:
        allowed_commands.update(extra_allowed)

    violations: List[LintViolation] = []
    blocks = extract_shell_blocks(content)

    for _, block_lines in blocks:
        logical_cmds = parse_logical_commands(block_lines)

        for line_no, cmd_line in logical_cmds:
            # 1. Check for command substitutions: `cmd` or $(cmd)
            if COMMAND_SUBSTITUTION_BACKTICKS.search(cmd_line):
                violations.append(
                    LintViolation(
                        file_path=file_path,
                        line_number=line_no,
                        command_snippet=cmd_line,
                        reason="Forbidden command substitution (`...`) detected.",
                    )
                )

            if COMMAND_SUBSTITUTION_DOLLAR.search(cmd_line):
                violations.append(
                    LintViolation(
                        file_path=file_path,
                        line_number=line_no,
                        command_snippet=cmd_line,
                        reason="Forbidden command substitution $(...) detected.",
                    )
                )

            # 2. Check for pipes to interpreters
            if FORBIDDEN_INTERPRETER_PIPE.search(cmd_line):
                violations.append(
                    LintViolation(
                        file_path=file_path,
                        line_number=line_no,
                        command_snippet=cmd_line,
                        reason="Forbidden piping to shell/interpreter (| sh, | bash, | python) detected.",
                    )
                )

            # 3. Check for unauthenticated download tools (curl, wget)
            if FORBIDDEN_DOWNLOADERS.search(cmd_line):
                violations.append(
                    LintViolation(
                        file_path=file_path,
                        line_number=line_no,
                        command_snippet=cmd_line,
                        reason="Unauthenticated download tool ('curl'/'wget') is forbidden in onboarding instructions.",
                    )
                )

            # 4. Check all sub-commands against the allowlist
            subcmds = split_subcommands(cmd_line)
            for sub_tokens in subcmds:
                exe = extract_executable_name(sub_tokens)
                if not exe:
                    continue

                if exe not in allowed_commands:
                    violations.append(
                        LintViolation(
                            file_path=file_path,
                            line_number=line_no,
                            command_snippet=" ".join(sub_tokens),
                            reason=f"Executable '{exe}' is not in the approved allowlist: {sorted(allowed_commands)}",
                        )
                    )

    return violations


def lint_file(file_path: Path, extra_allowed: Optional[Set[str]] = None) -> List[LintViolation]:
    """Lints a markdown file on disk."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        return [
            LintViolation(
                file_path=str(file_path),
                line_number=0,
                command_snippet="",
                reason=f"Failed to read file: {exc}",
            )
        ]

    return lint_markdown_content(content, file_path=str(file_path), extra_allowed=extra_allowed)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Onboarding Shell Command & Supply Chain Linter"
    )
    parser.add_argument("readme_files", nargs="+", help="README.md files to inspect")
    parser.add_argument(
        "--allow-cmd",
        action="append",
        default=[],
        help="Additional allowed command(s) (can be passed multiple times or comma-separated)",
    )

    args = parser.parse_args(argv)

    extra_allowed: Set[str] = set()
    for item in args.allow_cmd:
        for cmd in item.split(","):
            cleaned = cmd.strip().lower()
            if cleaned:
                extra_allowed.add(cleaned)

    all_violations: List[LintViolation] = []

    for file_str in args.readme_files:
        path = Path(file_str).resolve()
        if not path.is_file():
            print(f"⚠️  [SKIP] File not found: {file_str}", file=sys.stderr)
            continue

        violations = lint_file(path, extra_allowed=extra_allowed)
        all_violations.extend(violations)

        if not violations:
            print(f"✅ [PASS] {file_str}: all onboarding shell commands conform to security allowlist.")
        else:
            print(f"❌ [FAIL] {file_str}: {len(violations)} security violation(s) detected:")
            for v in violations:
                print(f"   - Line {v.line_number}: {v.reason}")
                print(f"     Snippet: {v.command_snippet}")

    if all_violations:
        print(f"\n🚫 [REJECTED] {len(all_violations)} total violation(s) found in onboarding commands.")
        return 1

    print("\n🎯 [SUCCESS] 100% of inspected onboarding commands are safe and allowlisted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

