#!/usr/bin/env python3
"""
skills/plan/scripts/validate_sdd_contracts.py
Validates architectural Software Design Description (SDD) specifications (SDD 2.0).

Enforces:
1. Markdown SDDs (.md):
   - Presence of all mandatory architectural sections (supporting both English and Portuguese).
   - Proper Mermaid sequence diagram syntax with double-quoted message labels.
   - Semantic Method Parity: methods invoked in Mermaid sequenceDiagram (->> / ->)
     must exist in the Mermaid classDiagram when both diagrams are present.
   - Semantic Error Parity: when BDD scenarios (@unhappy-path, @security, @concurrency)
     are provided via --bdd or embedded ```gherkin blocks, counts negative/edge scenario tags,
     verifies that the SDD models error branches (alt/else in sequenceDiagram), declares
     typed error/exception contracts, and when @security is present in BDD, ensures the SDD
     explicitly models security/auth error handling or status codes (401, 403, 422, *Error, *Exception, security).
2. YAML SDD Contracts (.yaml, .yml):
   - Valid YAML syntax and non-empty dictionary/mapping.
   - Presence of architectural contract structure (e.g. contracts, interfaces, version, etc.).
3. UTF-8 console encoding safety across Windows (cp1252 fix) and POSIX environments.
"""

import sys
import re
import argparse
from pathlib import Path
from typing import List, Optional, Set
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
        re.compile(r"##\s*(?:[^\n]*\b)?(?:Architecture\s*(?:&|and)\s*Contracts|Arquitetura\s*e\s*Contratos)\b", re.IGNORECASE),
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

HTTP_VERBS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


def extract_sequence_called_methods(seq_block: str) -> Set[str]:
    """
    Extracts method names invoked via solid call arrows (->> or ->) in a Mermaid sequenceDiagram.
    Ignores return arrows (-->>, -->), HTTP requests ("POST /..."), and non-method labels.
    """
    called_methods: Set[str] = set()
    for line in seq_block.splitlines():
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("%%"):
            continue
        # Only inspect forward call arrows (->> or ->), not dashed return arrows (-->> or -->)
        if "-->>" in line_clean or "-->" in line_clean or "--)" in line_clean:
            continue
        call_match = re.search(r"(?:->>|-\)|->)\s*([^:\n]+):\s*(.+)$", line_clean)
        if not call_match:
            continue
        raw_msg = call_match.group(2).strip().strip('"').strip("'")
        # Ignore HTTP endpoint calls like "POST /api/resource (DTO)"
        first_token = raw_msg.split()[0].upper() if raw_msg.split() else ""
        if first_token in HTTP_VERBS:
            continue
        # Match method call syntax: method_name(...) or obj.method_name(...)
        method_match = re.match(r"^(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", raw_msg)
        if method_match:
            called_methods.add(method_match.group(1))
    return called_methods


def extract_class_declared_methods(class_block: str) -> Set[str]:
    """
    Extracts method names declared inside a Mermaid classDiagram.
    Matches lines like '+register_user(req: DTO) Res' or 'save(entity: User) User'.
    """
    declared_methods: Set[str] = set()
    for line in class_block.splitlines():
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("%%") or line_clean.startswith("class "):
            continue
        method_match = re.match(r"^[+\-#~]?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", line_clean)
        if method_match:
            declared_methods.add(method_match.group(1))
    return declared_methods



def extract_class_method_signatures(class_block: str) -> Dict[str, Dict[str, Any]]:
    """
    Extracts method signatures with parameter types and return types from Mermaid classDiagram.
    Matches lines like:
      +register_user(req: CreateUserDTO) UserResponseDTO
      +find_by_id(user_id: UUID) Optional[User]
      +save(entity: User): User
    """
    signatures: Dict[str, Dict[str, Any]] = {}
    for line in class_block.splitlines():
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("%%") or line_clean.startswith("class "):
            continue
        m = re.match(
            r"^[+\-#~]?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)(?:\s*:?\s*([a-zA-Z0-9_\[\], \.]+))?",
            line_clean,
        )
        if m:
            method_name = m.group(1)
            raw_params = m.group(2).strip()
            return_type = (m.group(3) or "").strip()

            params: List[Tuple[str, str]] = []
            if raw_params:
                for p in raw_params.split(","):
                    p_clean = p.strip()
                    if ":" in p_clean:
                        p_name, p_type = p_clean.split(":", 1)
                        params.append((p_name.strip(), p_type.strip()))
                    else:
                        params.append((p_clean, "untyped"))

            signatures[method_name] = {
                "params": params,
                "return_type": return_type or "void",
                "raw": line_clean,
            }
    return signatures


def validate_method_signature_types(
    signatures: Dict[str, Dict[str, Any]],
    declared_dto_names: Set[str],
) -> List[str]:
    """
    Validates that declared class methods specify concrete parameter and return types
    matching declared YAML contracts/DTOs or standard scalar types.
    """
    errors: List[str] = []
    for m_name, sig in signatures.items():
        for p_name, p_type in sig["params"]:
            if p_type == "untyped":
                errors.append(
                    f"Signature Parity Error in method '{m_name}': parameter '{p_name}' lacks explicit type annotation."
                )
    return errors


def check_bijective_bdd_sdd_scenarios(
    bdd_content: str,
    sdd_content: str,
    sequence_blocks: List[str],
) -> List[str]:
    """
    Performs 1:1 bijective matching verifying that EVERY negative/security/concurrency scenario
    defined in BDD has an explicit corresponding exception or error handling branch in SDD.
    """
    errors: List[str] = []
    pattern = r"((?:@[a-zA-Z0-9_-]+\s+)*Scenario(?: Outline)?:\s*([^\n\r]+)(.*?))(?=(?:@[a-zA-Z0-9_-]+\s+)*Scenario|\Z)"
    matches = re.findall(pattern, bdd_content, re.DOTALL)

    for full, title, body in matches:
        is_negative = bool(re.search(r"@(?:unhappy-path|security|concurrency)\b", full, re.I))
        if not is_negative:
            continue

        scen_title = title.strip()
        exp_match = re.search(
            r"(?:raises?|throws?|lança|retorna|retornar|error|exception|status|código)\s+([A-Z][A-Za-z0-9_]*(?:Error|Exception)|\b(?:401|403|404|409|422|500)\b)",
            full,
            re.I,
        )
        if exp_match:
            expected_token = exp_match.group(1)
            token_in_sdd = bool(re.search(r"\b" + re.escape(expected_token) + r"\b", sdd_content, re.I))
            token_in_seq = any(bool(re.search(r"\b" + re.escape(expected_token) + r"\b", b, re.I)) for b in sequence_blocks)

            if not (token_in_sdd or token_in_seq):
                errors.append(
                    f"Bijective Parity Error (BDD -> SDD): Scenario '{scen_title}' specifies '{expected_token}', "
                    "but this exception/status code is not declared in SDD contracts or sequenceDiagram alt/else branches."
                )

    return errors

def check_bdd_sdd_error_parity(
    sdd_content: str,
    bdd_content: str,
    sequence_blocks: List[str],
) -> List[str]:
    """
    Verifies that when BDD specifications include @unhappy-path, @security, or @concurrency
    tags:
    1. Counts negative/edge scenario tags (@unhappy-path, @security, @concurrency) in bdd_content.
    2. Ensures sequenceDiagram has alt/else blocks and SDD declares error/exception contracts.
    3. If @security is present in BDD, ensures the SDD explicitly mentions security/auth error
       handling or status codes (e.g., 401, 403, 422, Auth*Error, Permission*Error, Security*Error,
       Unauthorized*, Forbidden*, or security:/authorization_scope).
    """
    errors: List[str] = []
    unhappy_tags = re.findall(r"@unhappy-path\b", bdd_content, re.IGNORECASE)
    security_tags = re.findall(r"@security\b", bdd_content, re.IGNORECASE)
    concurrency_tags = re.findall(r"@concurrency\b", bdd_content, re.IGNORECASE)

    negative_tags = unhappy_tags + security_tags + concurrency_tags
    negative_tag_count = len(negative_tags)
    if negative_tag_count == 0:
        return errors

    # Count alt/else/opt branches in sequenceDiagram blocks
    seq_branch_count = sum(
        len(re.findall(r"^\s*(?:alt|else|opt)\b", block, re.MULTILINE))
        for block in sequence_blocks
    )
    has_seq_alt_branch = seq_branch_count > 0

    # Check if SDD defines explicit exception classes or error contracts
    exception_matches = re.findall(
        r"\b(?:[A-Z][A-Za-z0-9_]*(?:Error|Exception)|exceptions\s*:|HTTP\s+4\d\d|status_code\s*:\s*4\d\d)\b",
        sdd_content,
    )
    has_exception_contract = len(exception_matches) > 0

    if sequence_blocks and not has_seq_alt_branch:
        errors.append(
            f"Semantic Parity Error (BDD <-> SDD): BDD defines {negative_tag_count} negative/edge scenario tag(s) "
            f"({sorted(set(t.lower() for t in negative_tags))}), "
            "but the Mermaid sequenceDiagram has no 'alt' / 'else' error branches."
        )
    if not has_exception_contract:
        errors.append(
            f"Semantic Parity Error (BDD <-> SDD): BDD defines {negative_tag_count} negative/edge scenario tag(s) "
            f"({sorted(set(t.lower() for t in negative_tags))}), "
            "but SDD contracts do not define any typed domain exceptions (*Error / *Exception) or HTTP 4xx error responses."
        )

    # Specific check when @security is present in BDD
    if security_tags:
        has_security_handling = bool(
            re.search(
                r"(?:\b(?:401|403|422)\b"
                r"|\b[A-Z][A-Za-z0-9_]*(?:Auth[A-Za-z0-9_]*|Security[A-Za-z0-9_]*|Permission[A-Za-z0-9_]*|Forbidden[A-Za-z0-9_]*|Unauthorized[A-Za-z0-9_]*|AccessDenied[A-Za-z0-9_]*|Token[A-Za-z0-9_]*|Role[A-Za-z0-9_]*)(?:Error|Exception)\b"
                r"|\b(?:UnauthorizedError|ForbiddenError|AuthenticationError|AuthorizationError|SecurityError|PermissionDeniedError|InvalidTokenError)\b"
                r"|\b(?:security\s*:|authorization_scope|rate_limit_tier|rbac|unauthorized|forbidden)\b)",
                sdd_content,
                re.IGNORECASE,
            )
        )
        if not has_security_handling:
            errors.append(
                f"Semantic Security Parity Error (BDD @security <-> SDD): BDD defines {len(security_tags)} '@security' scenario(s), "
                "but SDD does not specify any security/auth error handling, status codes (401, 403, 422), "
                "security exceptions (*Auth*Error, *Forbidden*Error, *Security*Error), or 'security:' contract metadata."
            )

    return errors


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


def validate_sdd_content(
    content: str,
    filepath_str: str,
    bdd_content: Optional[str] = None,
) -> bool:
    """Validates SDD text content against mandatory sections, Mermaid syntax, and semantic parity rules."""
    # If filepath indicates a YAML contract, delegate to YAML validator
    if filepath_str.lower().endswith((".yaml", ".yml")):
        return validate_sdd_yaml_content(content, filepath_str)

    errors: List[str] = []

    # 1. Section presence validation
    for section_name, pattern in MANDATORY_SECTION_PATTERNS:
        if not pattern.search(content):
            errors.append(f"Missing mandatory section: '{section_name}'")

    # 2. Mermaid diagram syntax & semantic parity validation
    sequence_blocks: List[str] = []
    class_blocks: List[str] = []

    if "```mermaid" in content:
        mermaid_blocks = re.findall(r"```mermaid\r?\n(.*?)```", content, re.DOTALL)
        for block in mermaid_blocks:
            if "sequenceDiagram" in block:
                sequence_blocks.append(block)
                for line in block.splitlines():
                    line_clean = line.strip()
                    if not line_clean or line_clean.startswith("%%"):
                        continue
                    arrow_match = re.search(r"(?:->>|-->>|-\)|--\)|->|-->)\s*([^:\n]+):\s*(.+)$", line_clean)
                    if arrow_match:
                        msg_text = arrow_match.group(2).strip()
                        if not (msg_text.startswith('"') and msg_text.endswith('"')):
                            errors.append(
                                f"Mermaid sequence diagram message label must be double-quoted. Line: '{line_clean}'"
                            )
            if "classDiagram" in block:
                class_blocks.append(block)

    # 3. Semantic Parity: sequenceDiagram methods <-> classDiagram methods
    if sequence_blocks and class_blocks:
        called_methods: Set[str] = set()
        for seq_b in sequence_blocks:
            called_methods.update(extract_sequence_called_methods(seq_b))

        declared_methods: Set[str] = set()
        for cls_b in class_blocks:
            declared_methods.update(extract_class_declared_methods(cls_b))

        if called_methods and declared_methods:
            unmapped_methods = sorted(called_methods - declared_methods)
            if unmapped_methods:
                errors.append(
                    "Semantic Parity Error (sequenceDiagram <-> classDiagram): "
                    f"Method(s) invoked in sequenceDiagram but missing from classDiagram: {unmapped_methods}"
                )

    # 4. Semantic Parity: BDD (@unhappy-path / @security / @concurrency) <-> SDD error handling
    effective_bdd = bdd_content
    if effective_bdd is None:
        gherkin_blocks = re.findall(r"```gherkin\r?\n(.*?)```", content, re.DOTALL)
        if gherkin_blocks:
            joined_gherkin = "\n".join(gherkin_blocks)
            # Only enforce embedded gherkin parity if it is not an unpopulated {{...}} template
            if "{{" not in joined_gherkin:
                effective_bdd = joined_gherkin

    if effective_bdd:
        errors.extend(check_bdd_sdd_error_parity(content, effective_bdd, sequence_blocks))
        errors.extend(check_bijective_bdd_sdd_scenarios(effective_bdd, content, sequence_blocks))

    # 5. Strict method signature typing in classDiagram
    all_signatures: Dict[str, Dict[str, Any]] = {}
    for cls_b in class_blocks:
        all_signatures.update(extract_class_method_signatures(cls_b))
    if all_signatures:
        errors.extend(validate_method_signature_types(all_signatures, set()))

    if errors:
        print(f"❌ [SDD Validation Failed] {filepath_str}:")
        for err in errors:
            print(f"   - {err}")
        return False

    print(f"✅ [SDD Validation Success] '{filepath_str}' strictly conforms to SDD 2.0 architectural standards.")
    return True


def validate_sdd_file(filepath: Path, bdd_filepath: Optional[Path] = None) -> bool:
    """Reads and validates an SDD file path (Markdown or YAML) and optional BDD companion file."""
    if not filepath.exists():
        print(f"❌ Error: Target SDD file does not exist: {filepath}")
        return False

    content = filepath.read_text(encoding="utf-8", errors="replace")
    if filepath.suffix.lower() in (".yaml", ".yml"):
        return validate_sdd_yaml_content(content, str(filepath))

    bdd_content: Optional[str] = None
    if bdd_filepath is not None:
        if not bdd_filepath.exists():
            print(f"❌ Error: Target BDD file does not exist: {bdd_filepath}")
            return False
        bdd_content = bdd_filepath.read_text(encoding="utf-8", errors="replace")

    return validate_sdd_content(content, str(filepath), bdd_content=bdd_content)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate SDD 2.0 architectural contracts (Markdown or YAML), Mermaid syntax, and BDD<->SDD semantic parity."
    )
    parser.add_argument(
        "filepath",
        nargs="?",
        default="implementation_plan.md",
        help="Path to SDD markdown or YAML file (default: implementation_plan.md)",
    )
    parser.add_argument(
        "--bdd",
        dest="bdd_filepath",
        default=None,
        help="Optional path to companion BDD specification file (01-concepcao/bdd-[slug].md) for cross-artifact semantic validation.",
    )
    args = parser.parse_args()

    target = Path(args.filepath)
    bdd_target = Path(args.bdd_filepath) if args.bdd_filepath else None
    success = validate_sdd_file(target, bdd_filepath=bdd_target)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
