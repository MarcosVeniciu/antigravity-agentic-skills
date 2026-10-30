#!/usr/bin/env python3
"""
workflows-skill/plan/scripts/validate_branch.py
Cross-platform Git Flow Branch Validator (Converted from legacy validate_branch.sh).

Enforces:
1. Rejection of protected base branches (main, master, develop, production).
2. Conformance with Git Flow naming conventions (feature/, feat/, bugfix/, fix/, refactor/, etc.)
   and strict lowercase alphanumeric + hyphen slug sanitization (preventing shell metacharacter injection).
3. Resilient Git discovery across Windows PowerShell and Unix terminals.
4. UTF-8 console encoding safety on Windows (cp1252 fix).
"""

import sys
import re
import subprocess
import argparse
from typing import Optional, Tuple

# Fix Windows cp1252 console crash when printing unicode emojis/symbols
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROTECTED_BASE_BRANCHES = {"main", "master", "develop", "production"}

VALID_BRANCH_REGEX = re.compile(
    r"^(feature|feat|bugfix|fix|hotfix|refactor|chore|docs|style|test|release)/[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*$"
)


def get_active_git_branch() -> Optional[str]:
    """Resiliently discovers the current active Git branch name."""
    try:
        res = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        pass

    # Fallback for detached HEAD or CI environments
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if res.returncode == 0 and res.stdout.strip() and res.stdout.strip() != "HEAD":
            return res.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        pass

    return None


def validate_branch_name(branch_name: str) -> Tuple[bool, str]:
    """Validates branch name against base branch locks, accepted prefixes, and strict slug safety."""
    clean_name = branch_name.strip()
    if not clean_name:
        return False, "Branch name is empty."

    # 1. Base Branch Phase Gate Lock
    if clean_name.lower() in PROTECTED_BASE_BRANCHES:
        return (
            False,
            f"⛔ [PHASE GATE LOCK]: You are currently on protected branch '{clean_name}'.\n"
            f"   Planning or implementing features directly on base branches is strictly prohibited.\n"
            f"   Please create a dedicated working branch: git checkout -b feature/<slug> (or feat/<slug>).",
        )

    # 2. Accepted Git Flow Regex Pattern (strict lowercase alphanumeric + single hyphen slug)
    if VALID_BRANCH_REGEX.match(clean_name):
        return True, f"✅ Success: Branch '{clean_name}' strictly adheres to project Git Flow and slug safety conventions."

    return (
        False,
        f"❌ Error: Branch name '{clean_name}' is invalid.\n"
        f"   Accepted prefix patterns: feature/*, feat/*, bugfix/*, fix/*, hotfix/*, "
        f"refactor/*, chore/*, docs/*, style/*, test/*, release/*\n"
        f"   Slug must strictly match '[a-z0-9]+(-[a-z0-9]+)*' (lowercase alphanumeric and hyphens only; no shell metacharacters or spaces).",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate current or specified Git branch against Git Flow conventions."
    )
    parser.add_argument(
        "branch",
        nargs="?",
        default=None,
        help="Optional branch name to validate. If omitted, discovers the active Git branch.",
    )
    parser.add_argument(
        "--branch",
        "-b",
        dest="branch_opt",
        default=None,
        help="Optional named argument for branch name.",
    )
    args = parser.parse_args()

    branch = args.branch_opt or args.branch
    if not branch:
        branch = get_active_git_branch()

    if not branch:
        print("❌ Error: Could not determine current Git branch. Ensure you are in an initialized Git repository.")
        return 1

    print(f"📊 Evaluating branch: '{branch}'")
    is_valid, msg = validate_branch_name(branch)
    print(msg)
    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
