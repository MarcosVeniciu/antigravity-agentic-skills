#!/usr/bin/env python3
"""
workflows-skill/release/scripts/validate_release.py
Cross-platform Release Readiness and SemVer Validator.

Enforces:
1. Conformance with SemVer 2.0.0 (vMAJOR.MINOR.PATCH with optional pre-release/build metadata).
2. Git branch naming conventions for releases (e.g., release/vX.Y.Z or release/X.Y.Z).
3. Existence and non-emptiness of changelog entries in CHANGELOG.md for the target version.
4. 100% Living DoD audit (zero unchecked boxes: '- [ ]') across candidate features.
5. Multiplatform UTF-8 console encoding safety on Windows (cp1252 fix).
"""

import sys
import os
import re
import glob
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Fix Windows cp1252 console crash when printing unicode emojis/symbols
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# SemVer 2.0.0 regular expression (official spec with optional 'v' prefix)
SEMVER_REGEX = re.compile(
    r"^v?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

RELEASE_BRANCH_REGEX = re.compile(
    r"^release/v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[\w.-]+)?$",
    re.IGNORECASE,
)


def validate_semver(version_str: str) -> Tuple[bool, str, Dict[str, str]]:
    """Validates a version string against Semantic Versioning 2.0.0."""
    clean_version = version_str.strip()
    if not clean_version:
        return False, "Version string is empty.", {}

    match = SEMVER_REGEX.match(clean_version)
    if not match:
        return (
            False,
            f"Version '{clean_version}' does not adhere to SemVer 2.0.0 (expected 'vMAJOR.MINOR.PATCH').",
            {},
        )

    return True, f"Version '{clean_version}' is valid SemVer 2.0.0.", match.groupdict()


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


def validate_branch_name(branch_name: str, target_version: Optional[str] = None) -> Tuple[bool, str]:
    """Validates release branch naming convention and optional version alignment."""
    clean_branch = branch_name.strip()
    if not clean_branch:
        return False, "Branch name is empty."

    if not RELEASE_BRANCH_REGEX.match(clean_branch):
        return (
            False,
            f"Branch name '{clean_branch}' is not a valid release branch. "
            f"Expected pattern: 'release/vX.Y.Z' or 'release/X.Y.Z'.",
        )

    if target_version:
        norm_branch_ver = clean_branch.split("/", 1)[1].lstrip("v")
        norm_target_ver = target_version.strip().lstrip("v")
        if norm_branch_ver != norm_target_ver:
            return (
                False,
                f"Branch version '{norm_branch_ver}' does not match target version '{norm_target_ver}'.",
            )

    return True, f"Branch '{clean_branch}' is a valid release branch conforming to conventions."


def validate_changelog_entry(changelog_path: Path, target_version: str) -> Tuple[bool, str]:
    """Verifies that CHANGELOG.md contains an entry and content for the target version."""
    if not changelog_path.exists():
        return False, f"Changelog file not found at '{changelog_path}'."

    try:
        content = changelog_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return False, f"Error reading changelog file '{changelog_path}': {e}"

    clean_ver = target_version.strip().lstrip("v")

    # Header regex matching:
    # ## [v1.2.0], ## [1.2.0], ## v1.2.0, ## 1.2.0, # Release Notes - v1.2.0, etc.
    header_pattern = re.compile(
        r"^(?P<hashes>#{1,3})\s+(?P<title>(?:\[\s*v?" + re.escape(clean_ver) + r"\s*\]|v?" + re.escape(clean_ver) + r"\b|Release\s+Notes\s*[-–—:]*\s*\[?\s*v?" + re.escape(clean_ver) + r"\b).*)$",
        re.MULTILINE | re.IGNORECASE,
    )

    match = header_pattern.search(content)
    if not match:
        return (
            False,
            f"No changelog entry header found for version '{target_version}' in '{changelog_path}'. "
            f"Expected header format such as '## [v{clean_ver}] - YYYY-MM-DD' or '# Release Notes - v{clean_ver}'.",
        )

    # Verify that the entry contains actual content before the next equal-or-higher level section
    header_level = len(match.group("hashes"))
    start_pos = match.end()

    next_section_pattern = re.compile(r"^#{1," + str(header_level) + r"}\s+", re.MULTILINE)
    next_match = next_section_pattern.search(content[start_pos:])

    body = content[start_pos : start_pos + next_match.start()] if next_match else content[start_pos:]
    clean_body = body.strip()

    if not clean_body:
        return (
            False,
            f"Changelog header for '{target_version}' exists in '{changelog_path}', but the section body is empty.",
        )

    return True, f"Valid changelog entry found for version '{target_version}' in '{changelog_path}'."


def validate_dod_files(patterns: List[str]) -> Tuple[bool, List[str]]:
    """Audits DoD files for 100% completion (zero unchecked checkboxes: '- [ ]')."""
    resolved_files: List[Path] = []
    for pat in patterns:
        for p in glob.glob(pat, recursive=True):
            resolved_files.append(Path(p))

    if not resolved_files:
        return True, ["No DoD files matched pattern. Skipping DoD verification."]

    errors: List[str] = []
    for dod_file in sorted(resolved_files):
        if not dod_file.is_file():
            continue
        try:
            lines = dod_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception as e:
            errors.append(f"Could not read DoD file '{dod_file}': {e}")
            continue

        unchecked = [
            f"Line {idx + 1}: {line.strip()}"
            for idx, line in enumerate(lines)
            if re.search(r"^\s*[-*]\s*\[\s*\]", line)
        ]

        if unchecked:
            errors.append(
                f"DoD file '{dod_file.name}' has {len(unchecked)} incomplete item(s):\n"
                + "\n".join(f"    {item}" for item in unchecked[:5])
                + (f"\n    ... and {len(unchecked) - 5} more." if len(unchecked) > 5 else "")
            )

    if errors:
        return False, errors
    return True, [f"All {len(resolved_files)} checked DoD file(s) are 100% complete (zero unchecked items)."]


def check_git_clean() -> Tuple[bool, str]:
    """Verifies that the Git working directory has no uncommitted changes."""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if res.returncode == 0:
            output = res.stdout.strip()
            if output:
                return False, f"Git working tree is dirty:\n{output}"
            return True, "Git working tree is clean."
    except Exception as e:
        return False, f"Could not check Git status: {e}"
    return True, "Git check skipped (not in a Git repository)."


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate SemVer format, release branch, changelog, and DoD completeness."
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Target release version string (e.g., 'v1.2.0' or '1.2.0').",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Release branch name to validate (e.g., 'release/v1.2.0'). If omitted, checks active branch.",
    )
    parser.add_argument(
        "--changelog",
        default="CHANGELOG.md",
        help="Path to CHANGELOG.md file (default: 'CHANGELOG.md').",
    )
    parser.add_argument(
        "--check-dod",
        nargs="*",
        default=[],
        help="Optional file path(s) or glob pattern(s) of Living DoD files to audit (e.g., '01-concepcao/dod-*.md').",
    )
    parser.add_argument(
        "--check-clean",
        action="store_true",
        help="Require clean Git working tree before proceeding.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: fail on any warning.",
    )

    args = parser.parse_args()

    print(f"🚀 Running Release Readiness Validation for version '{args.version}'...")
    has_errors = False

    # 1. Validate SemVer format
    valid_ver, ver_msg, _ = validate_semver(args.version)
    if not valid_ver:
        print(f"❌ [SEMVER ERROR] {ver_msg}")
        has_errors = True
    else:
        print(f"✅ [SEMVER OK] {ver_msg}")

    # 2. Validate Branch
    branch_to_check = args.branch or get_active_git_branch()
    if branch_to_check:
        valid_branch, branch_msg = validate_branch_name(branch_to_check, args.version)
        if not valid_branch:
            print(f"❌ [BRANCH ERROR] {branch_msg}")
            has_errors = True
        else:
            print(f"✅ [BRANCH OK] {branch_msg}")
    else:
        print("⚠️ [BRANCH NOTICE] No branch specified and active Git branch could not be determined.")
        if args.strict:
            has_errors = True

    # 3. Validate Changelog Entry
    changelog_path = Path(args.changelog)
    valid_cl, cl_msg = validate_changelog_entry(changelog_path, args.version)
    if not valid_cl:
        print(f"❌ [CHANGELOG ERROR] {cl_msg}")
        has_errors = True
    else:
        print(f"✅ [CHANGELOG OK] {cl_msg}")

    # 4. Validate DoD Completion (if requested)
    if args.check_dod:
        valid_dod, dod_msgs = validate_dod_files(args.check_dod)
        if not valid_dod:
            print("❌ [DOD AUDIT FAILED]")
            for err in dod_msgs:
                print(f"   {err}")
            has_errors = True
        else:
            for msg in dod_msgs:
                print(f"✅ [DOD AUDIT OK] {msg}")

    # 5. Check Git Working Tree (if requested)
    if args.check_clean:
        clean_ok, clean_msg = check_git_clean()
        if not clean_ok:
            print(f"❌ [GIT STATUS ERROR] {clean_msg}")
            has_errors = True
        else:
            print(f"✅ [GIT STATUS OK] {clean_msg}")

    print("----------------------------------------------------------------------")
    if has_errors:
        print(f"❌ Release validation FAILED for '{args.version}'. Fix the issues above before releasing.")
        return 1

    print(f"🎉 Release validation PASSED for '{args.version}'! Ready for Git Flow finalization.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
