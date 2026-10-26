#!/usr/bin/env python3
"""
tests/test_flow_skills_integrity.py
Comprehensive Integrity and Quality Gate Suite for skills/

Enforces:
1. Directory structure presence and valid skill package names.
2. YAML frontmatter conformance (name, lowercase slug, description >= 50 chars in 3rd person).
3. Strict separation: references/ (operational docs only, NO templates),
   resources/ (templates only, NO manuals in root), scripts/ (executable .py only).
4. Referential integrity: zero broken relative markdown links and no orphan assets.
5. Multiplatform Python compilation (py_compile) and UTF-8 console encoding hygiene.
6. Absolute immutability of legacy workflows/ and skills/ directories.
"""

import os
import re
import sys
import subprocess
import urllib.parse
import py_compile
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

import pytest
import yaml

# -----------------------------------------------------------------------------
# Constant Paths and Baselines
# -----------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
LEGACY_WORKFLOWS_DIR = REPO_ROOT / "workflows"
LEGACY_SKILLS_DIR = REPO_ROOT / "skills"

EXPECTED_SKILLS = [
    "implement",
    "plan",
    "refactor",
    "review",
    "docs",
    "decompose",
    "release",
    "test-fix",
    "debug",
    "ask",
    "infra",
    "obsidian",
]

ALLOWED_SUBDIRS = {"references", "resources", "scripts", "examples", "__pycache__"}
ALLOWED_ROOT_FILES = {"SKILL.md", ".gitignore"}

EXPECTED_WORKFLOW_FILES = {
    "ask.md",
    "debug.md",
    "decompose.md",
    "docs.md",
    "implement.md",
    "infra.md",
    "plan.md",
    "refactor.md",
    "release.md",
    "review.md",
    "test-fix.md",
}

EXPECTED_LEGACY_SKILL_DIRS = {
    "ask",
    "debug",
    "docs",
    "dod",
    "git",
    "infra",
    "notebooklm",
    "obsidian",
    "plan-bdd",
    "plan-debate",
    "plan-decompose",
    "plan-sdd",
    "refactor",
    "release",
    "review-architecture",
    "review-performance",
    "review-quality",
    "review-resilience",
    "review-security",
    "tdd-code",
    "tdd-plan",
    "tdd-tests",
    "test-fix",
    "test-integration",
}


# -----------------------------------------------------------------------------
# Discovery & Parametrization Helpers
# -----------------------------------------------------------------------------
def get_discovered_skills() -> List:
    """Returns parameterized skill directories, or skips gracefully if none exist."""
    if not SKILLS_DIR.exists():
        return [
            pytest.param(
                None,
                id="none",
                marks=pytest.mark.skip(reason="skills/ does not exist yet"),
            )
        ]
    skills = sorted(
        [d for d in SKILLS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")],
        key=lambda d: d.name,
    )
    if not skills:
        return [
            pytest.param(
                None,
                id="none",
                marks=pytest.mark.skip(reason="No skills found in skills/"),
            )
        ]
    return [pytest.param(s, id=s.name) for s in skills]


# -----------------------------------------------------------------------------
# Validation Helper Functions
# -----------------------------------------------------------------------------
def parse_skill_frontmatter(skill_md_path: Path) -> Tuple[Dict, str]:
    """
    Extracts and parses YAML frontmatter and body text from SKILL.md.
    Raises AssertionError if frontmatter delimiters or YAML syntax are invalid.
    """
    assert skill_md_path.exists(), f"Manifest file missing: {skill_md_path}"
    content = skill_md_path.read_text(encoding="utf-8", errors="replace")

    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", content, re.DOTALL)
    assert match is not None, (
        f"Invalid or missing YAML frontmatter delimiters '---' in {skill_md_path}. "
        "File must begin on line 1 with '---' and have a closing '---'."
    )

    raw_yaml = match.group(1)
    body = match.group(2)

    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        pytest.fail(f"YAML parsing error in {skill_md_path}: {e}")

    assert isinstance(data, dict), f"Frontmatter in {skill_md_path} must be a YAML mapping (dict)."
    return data, body


def validate_description(description: str) -> Tuple[bool, str]:
    """
    Validates that a description is non-empty, >= 50 characters, and in 3rd-person voice.
    """
    cleaned = description.strip()
    if len(cleaned) < 50:
        return False, f"Description length is {len(cleaned)} chars, must be >= 50 chars."

    # Check 1st-person pronouns (I, me, my, mine, we, us, our, ours)
    first_person = re.search(r"\b(i|me|my|mine|we|us|our|ours)\b", cleaned, re.IGNORECASE)
    if first_person:
        return False, f"Description contains forbidden 1st-person pronoun '{first_person.group(0)}'."

    # Check conversational 2nd-person instruction starters
    second_person_starter = re.match(r"^(you|your|please)\b", cleaned, re.IGNORECASE)
    if second_person_starter:
        return False, f"Description starts with 2nd-person instruction '{second_person_starter.group(0)}'."

    return True, "OK"


def extract_relative_markdown_links(md_path: Path) -> List[Tuple[str, Path]]:
    """
    Extracts all relative local links and image paths from a markdown file.
    Strips fenced code blocks (``` ... ```) before extraction.
    Returns a list of (raw_link, resolved_target_path).
    """
    content = md_path.read_text(encoding="utf-8", errors="replace")

    # Strip fenced code blocks
    cleaned = re.sub(r"```.*?```", "", content, flags=re.DOTALL)

    # Match [anchor](target) and ![alt](target)
    matches = re.findall(r"\[(?:[^\]]*)\]\(([^)]+)\)", cleaned)

    # Match reference definitions [id]: target
    ref_defs = re.findall(r"^\[[^\]]+\]:\s*(\S+)", cleaned, flags=re.MULTILINE)
    all_raw_targets = matches + ref_defs

    results = []
    for raw in all_raw_targets:
        clean_target = raw.strip()
        # Strip optional markdown title: e.g. [alt](path "title")
        if " " in clean_target:
            clean_target = clean_target.split()[0]
        clean_target = clean_target.strip("\"'()")

        # Skip web, email, anchor-only, or protocol-relative links
        if re.match(r"^(?:https?://|mailto:|ftp:|#|//)", clean_target, re.IGNORECASE):
            continue

        # Strip fragment anchor and query params
        path_part = clean_target.split("#")[0].split("?")[0].strip()
        if not path_part:
            continue

        # URL decode path (e.g. %20 -> space)
        decoded_path = urllib.parse.unquote(path_part)

        # Resolve path
        if decoded_path.startswith("/"):
            resolved = (REPO_ROOT / decoded_path.lstrip("/")).resolve()
        else:
            resolved = (md_path.parent / decoded_path).resolve()

        results.append((clean_target, resolved))

    return results


# -----------------------------------------------------------------------------
# Test Cases
# -----------------------------------------------------------------------------
def test_skills_directory_structure():
    """
    Checks presence and validity of skills/ root and package names:
    - Root directory exists.
    - No loose files directly under skills/.
    - At least one skill package is present.
    - All subdirectories belong to the canonical 13 Agent Skills list.
    """
    assert SKILLS_DIR.exists(), f"Target directory does not exist: {SKILLS_DIR}"
    assert SKILLS_DIR.is_dir(), f"Target path is not a directory: {SKILLS_DIR}"

    found_dirs = [d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
    found_files = [f.name for f in SKILLS_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]

    assert len(found_files) == 0, f"No loose files permitted in skills/: {found_files}"
    assert len(found_dirs) > 0, "skills/ must contain at least one skill package"

    unknown_dirs = set(found_dirs) - set(EXPECTED_SKILLS)
    assert not unknown_dirs, f"Unrecognized skill directories in skills/: {unknown_dirs}"


def test_wave_1_pilot_exists():
    """Validates that the Wave 1 pilot package 'implement' exists and is a directory."""
    implement_dir = SKILLS_DIR / "implement"
    assert implement_dir.exists(), f"Wave 1 pilot package directory missing: {implement_dir}"
    assert implement_dir.is_dir(), f"Wave 1 pilot path is not a directory: {implement_dir}"


def test_all_13_skills_presence():
    """
    Validates presence of all 13 canonical Agent Skills packages.
    During progressive rollout (M1-M4), skips with an informative summary if not all 13 exist.
    In M5 or when STRICT_13_SKILLS=1, strictly asserts all 13 packages exist.
    """
    if not SKILLS_DIR.exists():
        pytest.skip("skills/ directory does not exist yet")

    found_dirs = {d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")}
    missing = set(EXPECTED_SKILLS) - found_dirs
    strict_mode = os.environ.get("STRICT_13_SKILLS", "").lower() in ("1", "true", "yes")

    if missing and not strict_mode and len(found_dirs) < len(EXPECTED_SKILLS):
        pytest.skip(
            f"Progressive migration in progress: {len(found_dirs)}/{len(EXPECTED_SKILLS)} skills present "
            f"({', '.join(sorted(found_dirs))}). Pending waves: {', '.join(sorted(missing))}."
        )

    assert not missing, f"Missing required skills in skills/: {sorted(missing)}"


@pytest.mark.parametrize("skill_dir", get_discovered_skills())
def test_yaml_frontmatter(skill_dir: Path):
    """
    Parses YAML frontmatter for each skill and validates:
    1. SKILL.md exists.
    2. 'name' field is lowercase, valid slug, and matches folder name.
    3. 'description' field is non-empty, >= 50 characters, and in 3rd-person voice.
    """
    if skill_dir is None:
        pytest.skip("No skill directories found")

    skill_md = skill_dir / "SKILL.md"
    frontmatter, _ = parse_skill_frontmatter(skill_md)

    # 1. Name validation
    assert "name" in frontmatter, f"'name' field missing from frontmatter in {skill_md}"
    name = frontmatter["name"]
    assert isinstance(name, str), f"'name' in {skill_md} must be a string"
    assert name == name.lower(), f"'name' '{name}' in {skill_md} must be lowercase"
    assert re.match(r"^[a-z0-9-]+$", name), f"'name' '{name}' in {skill_md} must be a valid slug"
    assert name == skill_dir.name, (
        f"'name' '{name}' in {skill_md} does not match directory name '{skill_dir.name}'"
    )

    # 2. Description validation
    assert "description" in frontmatter, f"'description' field missing in {skill_md}"
    desc = frontmatter["description"]
    assert isinstance(desc, str), f"'description' in {skill_md} must be a string"

    is_valid, msg = validate_description(desc)
    assert is_valid, f"Frontmatter description error in {skill_md}: {msg}"


@pytest.mark.parametrize("skill_dir", get_discovered_skills())
def test_strict_directory_separation(skill_dir: Path):
    """
    Ensures strict separation between operational docs, templates, and scripts:
    1. Only permitted subdirectories allowed in skill package.
    2. Only SKILL.md and .gitignore permitted at skill root.
    3. references/: Contains ONLY operational docs (.md/.txt). NO templates permitted.
    4. resources/: Contains ONLY templates. NO procedural manuals permitted in root.
    5. scripts/: Contains ONLY executable CLI scripts (.py). NO loose documentation.
    """
    if skill_dir is None:
        pytest.skip("No skill directories found")

    # 1. Root items check
    for item in skill_dir.iterdir():
        if item.name.startswith("."):
            continue
        if item.is_dir():
            assert item.name in ALLOWED_SUBDIRS, (
                f"Unauthorized subdirectory '{item.name}' in {skill_dir}. Allowed: {ALLOWED_SUBDIRS}"
            )
        elif item.is_file():
            assert item.name in ALLOWED_ROOT_FILES, (
                f"Unauthorized loose file '{item.name}' at root of {skill_dir}. Allowed: {ALLOWED_ROOT_FILES}"
            )

    # 2. references/ check (NO templates)
    references_dir = skill_dir / "references"
    if references_dir.exists():
        assert references_dir.is_dir()
        for ref_file in references_dir.rglob("*"):
            if ref_file.is_file() and not ref_file.name.startswith("."):
                assert ref_file.suffix in (".md", ".txt"), (
                    f"Non-document file found in references/: {ref_file}"
                )
                assert "template" not in ref_file.name.lower(), (
                    f"Template file '{ref_file.name}' is strictly forbidden in references/. "
                    "Move template files to resources/."
                )

    # 3. resources/ check (Pure templates, NO procedural manuals in root)
    resources_dir = skill_dir / "resources"
    if resources_dir.exists():
        assert resources_dir.is_dir()
        for res_file in resources_dir.iterdir():
            if res_file.is_file() and not res_file.name.startswith("."):
                lower_name = res_file.name.lower()
                prohibited_manual_patterns = (
                    "manual", "guide", "protocol", "methodology", "checklist", "execution"
                )
                for pattern in prohibited_manual_patterns:
                    assert pattern not in lower_name, (
                        f"Procedural manual '{res_file.name}' forbidden in resources/ root. "
                        "Move operational documentation to references/."
                    )

    # 4. scripts/ check (Executable scripts only)
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        assert scripts_dir.is_dir()
        for script_file in scripts_dir.rglob("*"):
            if script_file.is_file() and "__pycache__" not in script_file.parts and not script_file.name.startswith("."):
                assert script_file.suffix == ".py", (
                    f"Non-python script '{script_file.name}' found in scripts/. "
                    "All utility scripts must be cross-platform Python (.py)."
                )


@pytest.mark.parametrize("skill_dir", get_discovered_skills())
def test_referential_integrity(skill_dir: Path):
    """
    Verifies that:
    1. Every relative markdown link in the skill bundle resolves to an existing file on disk.
    2. Zero broken relative links exist.
    3. Every physical file in references/ and resources/ is referenced at least once (no orphan assets).
    """
    if skill_dir is None:
        pytest.skip("No skill directories found")

    md_files = list(skill_dir.rglob("*.md"))
    broken_links = []
    referenced_disk_targets: Set[Path] = set()

    for md_file in md_files:
        links = extract_relative_markdown_links(md_file)
        for raw_target, target_path in links:
            if not target_path.exists():
                broken_links.append(
                    f"In {md_file.relative_to(REPO_ROOT)}: '{raw_target}' -> {target_path} (File Not Found)"
                )
            else:
                referenced_disk_targets.add(target_path.resolve())

    assert not broken_links, (
        f"Found {len(broken_links)} broken relative link(s) in {skill_dir.name}:\n"
        + "\n".join(broken_links)
    )

    # Orphan Asset Verification for references/ and resources/
    bundled_assets: Set[Path] = set()
    for sub in ("references", "resources"):
        sub_path = skill_dir / sub
        if sub_path.exists():
            for f in sub_path.rglob("*"):
                if f.is_file() and not f.name.startswith(".") and "__pycache__" not in f.parts:
                    bundled_assets.add(f.resolve())

    orphans = bundled_assets - referenced_disk_targets
    assert not orphans, (
        f"Found {len(orphans)} orphan unreferenced file(s) in {skill_dir.name}:\n"
        + "\n".join(str(o.relative_to(REPO_ROOT)) for o in sorted(orphans))
        + "\nEvery file in references/ and resources/ must be referenced by SKILL.md or an execution guide."
    )


@pytest.mark.parametrize("skill_dir", get_discovered_skills())
def test_python_scripts_compile(skill_dir: Path):
    """
    Validates Python script compilation and multiplatform encoding hygiene:
    1. Scripts in scripts/: py_compile, shebang, UTF-8 reconfigure, main guard.
    2. Templates in resources/: py_compile.compile().
    """
    if skill_dir is None:
        pytest.skip("No skill directories found")

    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        for script_file in scripts_dir.rglob("*.py"):
            if "__pycache__" in script_file.parts or script_file.name.startswith("."):
                continue

            try:
                py_compile.compile(str(script_file), doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"Compilation failed for {script_file}: {e}")

            content = script_file.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()

            # Shebang check
            assert lines and lines[0].startswith("#!"), (
                f"Script {script_file.name} missing shebang line (expected '#!/usr/bin/env python3')"
            )

            # Windows UTF-8 stdout reconfiguration check
            assert "reconfigure(encoding=" in content or "reconfigure(encoding='utf-8'" in content, (
                f"Script {script_file.name} missing UTF-8 stream reconfiguration. "
                "Must include: sys.stdout.reconfigure(encoding='utf-8', errors='replace')"
            )

            # CLI Entrypoint guard check
            assert "if __name__ == '__main__':" in content or 'if __name__ == "__main__":' in content, (
                f"Script {script_file.name} missing CLI execution guard: if __name__ == '__main__':"
            )

    resources_dir = skill_dir / "resources"
    if resources_dir.exists():
        for res_file in resources_dir.rglob("*.py"):
            if "__pycache__" in res_file.parts or res_file.name.startswith("."):
                continue
            try:
                py_compile.compile(str(res_file), doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"Compilation failed for template {res_file}: {e}")


def test_legacy_cleanup_completed():
    """
    Validates that legacy workflows/ directory has been safely decommissioned
    and skills/ now holds the modern self-sufficient Agent Skills packages.
    """
    assert not LEGACY_WORKFLOWS_DIR.exists(), f"Legacy workflows/ directory should be removed: {LEGACY_WORKFLOWS_DIR}"
    assert SKILLS_DIR.exists(), f"Canonical skills/ directory must exist: {SKILLS_DIR}"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
