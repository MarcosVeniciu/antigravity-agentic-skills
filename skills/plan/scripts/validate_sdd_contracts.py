#!/usr/bin/env python3
"""
workflows-skill/plan/scripts/validate_sdd_contracts.py
Validates architectural Software Design Description (SDD) specifications.

Enforces:
1. Markdown SDDs (.md):
   - Presence of all mandatory architectural sections (supporting both English and Portuguese).
   - Proper Mermaid sequence diagram syntax with double-quoted message labels.
2. YAML SDD Contracts (.yaml, .yml):
   - Valid YAML syntax and non-empty dictionary/mapping.
   - Presence of architectural contract structure (e.g. contracts, interfaces, version, etc.).
3. UTF-8 console encoding safety across Windows (cp1252 fix) and POSIX environments.
"""

import sys
import re
import argparse
from pathlib import Path
import yaml

# Fix Windows cp1252 console crash when printing unicode emojis/symbols
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


MANDATORY_SECTION_PATTERNS = [
    (
        "Technical Goal / Objetivo Técnico",
        re.compile(r"##\s*(?:[^\n]*\b)?(?:Technical\s+Goal|Objetivo\s+T[ée]cnico)\b", re.IGNORECASE),
    ),
    (
        "Sequential Implementation Plan / Plano Sequencial",
        re.compile(r"##\s*(?:[^\n]*\b)?(?:Sequential\s+Implementation\s+Plan|Plano\s+Sequencial)\b", re.IGNORECASE),
    ),
    (
        "Architecture & Contracts / Arquitetura e Contratos",
        re.compile(r"##\s*(?:[^\n]*\b)?(?:Architecture\s*&\s*Contracts|Arquitetura\s*e\s*Contratos)\b", re.IGNORECASE),
    ),
    (
        "File Impact Analysis / Análise de Impacto",
        re.compile(r"##\s*(?:[^\n]*\b)?(?:File\s+Impact(?:\s+Analysis)?|An[áa]lise\s+de\s+Impacto)\b", re.IGNORECASE),
    ),
]

YAML_CONTRACT_KEYS = {
    "contract",
    "contracts",
    "version",
    "schema_version",
    "entities",
    "interfaces",
    "models",
    "dto",
    "services",
    "types",
}


def validate_sdd_yaml_content(content: str, filepath_str: str) -> bool:
    """Validates pure YAML SDD contract content."""
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        print(f"❌ [SDD YAML Contract Validation Error] {filepath_str}: Syntax error in YAML:\n   {exc}")
        return False
    except Exception as exc:
        print(f"❌ [SDD YAML Contract Validation Error] {filepath_str}: Failed to parse YAML:\n   {exc}")
        return False

    if not isinstance(data, dict) or not data:
        print(
            f"❌ [SDD YAML Contract Validation Error] {filepath_str}: "
            f"Parsed data must be a non-empty dictionary/mapping."
        )
        return False

    keys_lower = {str(k).strip().lower() for k in data.keys()}
    has_contract_structure = any(
        k in YAML_CONTRACT_KEYS or "contract" in k or "version" in k
        for k in keys_lower
    )

    if not has_contract_structure:
        print(
            f"❌ [SDD YAML Contract Validation Error] {filepath_str}: "
            f"Missing required contract structure. Expected at least one of keys: {sorted(YAML_CONTRACT_KEYS)}"
        )
        return False

    print(f"✅ [SDD YAML Contract Validation Success]: {filepath_str}")
    return True


def validate_sdd_content(content: str, filepath_str: str) -> bool:
    """Validates SDD text content against mandatory sections and Mermaid rules."""
    # If filepath indicates a YAML contract, delegate to YAML validator
    if filepath_str.lower().endswith((".yaml", ".yml")):
        return validate_sdd_yaml_content(content, filepath_str)

    errors = []

    # 1. Section presence validation
    for section_name, pattern in MANDATORY_SECTION_PATTERNS:
        if not pattern.search(content):
            errors.append(f"Missing mandatory section: '{section_name}'")

    # 2. Mermaid diagram validation
    if "```mermaid" in content:
        mermaid_blocks = re.findall(r"```mermaid\r?\n(.*?)```", content, re.DOTALL)
        for block in mermaid_blocks:
            # Check for sequence diagram unquoted message labels
            if "sequenceDiagram" in block:
                # Find messages like A->>B: message without quotes
                for line in block.splitlines():
                    line_clean = line.strip()
                    if not line_clean or line_clean.startswith("%%"):
                        continue
                    # Match arrows: ->>, -->>, -), --), ->, -->
                    arrow_match = re.search(r"(?:->>|-->>|-\)|--\)|->|-->)\s*([^:\n]+):\s*(.+)$", line_clean)
                    if arrow_match:
                        msg_text = arrow_match.group(2).strip()
                        if not (msg_text.startswith('"') and msg_text.endswith('"')):
                            errors.append(
                                f"Mermaid sequence diagram message label must be double-quoted. Line: '{line_clean}'"
                            )

    if errors:
        print(f"❌ [SDD Validation Failed] {filepath_str}:")
        for err in errors:
            print(f"   - {err}")
        return False

    print(f"✅ [SDD Validation Success] '{filepath_str}' strictly conforms to architectural standards.")
    return True


def validate_sdd_file(filepath: Path) -> bool:
    """Reads and validates an SDD file path (Markdown or YAML)."""
    if not filepath.exists():
        print(f"❌ Error: Target SDD file does not exist: {filepath}")
        return False

    content = filepath.read_text(encoding="utf-8", errors="replace")
    if filepath.suffix.lower() in (".yaml", ".yml"):
        return validate_sdd_yaml_content(content, str(filepath))
    return validate_sdd_content(content, str(filepath))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate SDD architectural contracts (Markdown or YAML) and Mermaid syntax."
    )
    parser.add_argument(
        "filepath",
        nargs="?",
        default="implementation_plan.md",
        help="Path to SDD markdown or YAML file (default: implementation_plan.md)",
    )
    args = parser.parse_args()

    target = Path(args.filepath)
    success = validate_sdd_file(target)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

