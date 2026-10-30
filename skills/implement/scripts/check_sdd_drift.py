#!/usr/bin/env python3
"""
skills/implement/scripts/check_sdd_drift.py
SDD 2.0 Drift Gate Validator — Enforces Code <-> SDD Specification Parity.

Compares implemented production code (.py via AST; .ts/.js/.dart via regex)
against the approved Software Design Description (01-concepcao/sdd-[slug].md or .yaml):
1. Class, Interface (<<Interface>>), and Exception (*Error / *Exception) presence.
2. Public method parity between Mermaid classDiagram / YAML interfaces and actual classes.
3. Optional File Impact Analysis drift check (--check-files) against planned SDD file paths.
4. Respects documented technical pivots (--pivots 02-auditorias/pivots-[slug].md) with
   rigid YAML schema (authorized_by: "human") so formally recorded deviations pass
   as authorized pivots rather than silent spec drift.
"""

import ast
import sys
import re
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class SddSpecContract:
    """Represents the architectural contracts extracted from an SDD specification."""
    classes_and_methods: Dict[str, Set[str]] = field(default_factory=dict)
    exceptions: Set[str] = field(default_factory=set)
    planned_files: Set[str] = field(default_factory=set)


@dataclass
class DriftFinding:
    category: str  # MISSING_CLASS | MISSING_METHOD | MISSING_EXCEPTION | UNPLANNED_FILE
    symbol: str
    details: str
    authorized_by_pivot: bool = False


def parse_mermaid_class_diagrams(sdd_text: str) -> Dict[str, Set[str]]:
    """
    Extracts class/interface definitions and their public methods from Mermaid classDiagram blocks.
    Ignores private/protected attributes and methods starting with '-', '#', '~', or '_'.
     Ignores test doubles (<<Fake>>, <<Mock>>, <<Stub>>, InMemory*, Fake*, Mock*) by default
    when checking production code, unless they are also in target files.
    """
    classes: Dict[str, Set[str]] = {}
    mermaid_blocks = re.findall(r"```mermaid\r?\n(.*?)```", sdd_text, re.DOTALL)

    for block in mermaid_blocks:
        if "classDiagram" not in block:
            continue

        # Match `class ClassName { ... }` blocks
        class_body_matches = re.finditer(
            r"class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{([^}]*)\}",
            block,
            re.DOTALL,
        )
        for match in class_body_matches:
            cls_name = match.group(1)
            body = match.group(2)
            # Skip in-memory test doubles from mandatory production class requirement
            if (
                "<<Fake>>" in body
                or "<<Mock>>" in body
                or cls_name.startswith(("InMemory", "Fake", "Mock"))
            ):
                continue

            methods = classes.setdefault(cls_name, set())
            for raw_line in body.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("%%") or line.startswith("<<"):
                    continue
                # Skip private/protected members
                if line[0] in ("-", "#", "~"):
                    continue
                m_match = re.match(r"^\+?\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
                if m_match:
                    m_name = m_match.group(1)
                    if not m_name.startswith("_"):
                        methods.add(m_name)

    return classes


def parse_yaml_contracts(yaml_text: str, spec: SddSpecContract) -> None:
    """Extracts interfaces, methods, and exceptions from a YAML contract dictionary."""
    try:
        data = yaml.safe_load(yaml_text)
    except Exception:
        return

    if not isinstance(data, dict):
        return

    # Extract interfaces and their methods
    interfaces = data.get("interfaces", [])
    if isinstance(interfaces, list):
        for iface in interfaces:
            if not isinstance(iface, dict):
                continue
            iface_name = iface.get("name")
            if not iface_name or "{{" in str(iface_name):
                continue
            methods_set = spec.classes_and_methods.setdefault(str(iface_name), set())
            for m in iface.get("methods", []):
                if isinstance(m, dict) and m.get("name"):
                    m_name = str(m["name"])
                    if "{{" not in m_name and not m_name.startswith("_"):
                        methods_set.add(m_name)

    # Extract declared exceptions under contracts
    contracts = data.get("contracts", [])
    if isinstance(contracts, list):
        for contract in contracts:
            if not isinstance(contract, dict):
                continue
            for exc in contract.get("exceptions", []):
                if isinstance(exc, dict) and exc.get("name"):
                    exc_name = str(exc["name"])
                    if "{{" not in exc_name:
                        spec.exceptions.add(exc_name)


def parse_planned_files(sdd_text: str) -> Set[str]:
    """Extracts file paths from the File Impact Analysis markdown table."""
    planned: Set[str] = set()
    # Look for backticked file paths inside markdown table rows
    for line in sdd_text.splitlines():
        line_s = line.strip()
        if not line_s.startswith("|"):
            continue
        cells = [c.strip() for c in line_s.strip("|").split("|")]
        if not cells:
            continue
        first_cell = cells[0]
        path_match = re.search(r"`([^`]+\.[a-zA-Z0-9]+)`", first_cell)
        if path_match:
            raw_path = path_match.group(1).strip().replace("\\", "/")
            if "{{" not in raw_path:
                planned.add(raw_path)
    return planned


def extract_sdd_spec(sdd_path: Path) -> SddSpecContract:
    """Parses a Markdown or YAML SDD specification into an SddSpecContract."""
    spec = SddSpecContract()
    content = sdd_path.read_text(encoding="utf-8", errors="replace")

    if sdd_path.suffix.lower() in (".yaml", ".yml"):
        parse_yaml_contracts(content, spec)
        return spec

    # Parse Mermaid classDiagrams
    mermaid_classes = parse_mermaid_class_diagrams(content)
    for cls_name, methods in mermaid_classes.items():
        spec.classes_and_methods.setdefault(cls_name, set()).update(methods)

    # Parse embedded ```yaml blocks
    yaml_blocks = re.findall(r"```ya?ml\r?\n(.*?)```", content, re.DOTALL)
    for y_block in yaml_blocks:
        parse_yaml_contracts(y_block, spec)

    # Parse File Impact Analysis table
    spec.planned_files = parse_planned_files(content)
    return spec


def extract_code_symbols_from_python(py_path: Path) -> Tuple[Dict[str, Set[str]], Optional[str]]:
    """Uses Python AST to extract defined classes and their methods from a .py file."""
    classes: Dict[str, Set[str]] = {}
    try:
        source = py_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(py_path))
    except Exception as exc:
        return classes, f"Failed to parse {py_path}: {exc}"

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = classes.setdefault(node.name, set())
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.add(item.name)

    return classes, None


def extract_code_symbols_from_polyglot(file_path: Path) -> Tuple[Dict[str, Set[str]], Optional[str]]:
    """Extracts class/interface names and method names from .ts, .js, .dart files via regex."""
    classes: Dict[str, Set[str]] = {}
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return classes, f"Failed to read {file_path}: {exc}"

    # Match class or interface blocks
    cls_matches = re.finditer(
        r"\b(?:class|interface|abstract\s+class)\s+([A-Za-z_][A-Za-z0-9_]*)[^{]*\{([^}]*)\}",
        content,
        re.DOTALL,
    )
    for m in cls_matches:
        cls_name = m.group(1)
        body = m.group(2)
        methods = classes.setdefault(cls_name, set())
        for m_match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", body):
            name = m_match.group(1)
            if name not in ("if", "for", "while", "switch", "catch", "constructor", cls_name):
                methods.add(name)

    return classes, None


def collect_implemented_symbols(
    targets: List[Path],
) -> Tuple[Dict[str, Set[str]], List[Path], List[str]]:
    """
    Scans target files/directories and returns:
    - implemented_classes: mapping of ClassName -> set of method names
    - scanned_files: list of code files scanned
    - parse_errors: list of file read/parse errors
    """
    implemented_classes: Dict[str, Set[str]] = {}
    scanned_files: List[Path] = []
    parse_errors: List[str] = []
    supported_exts = (".py", ".ts", ".tsx", ".js", ".jsx", ".dart")

    for target in targets:
        if target.is_file():
            if target.suffix.lower() in supported_exts:
                scanned_files.append(target)
        elif target.is_dir():
            for ext in supported_exts:
                scanned_files.extend(target.glob(f"**/*{ext}"))

    for fpath in scanned_files:
        if fpath.suffix.lower() == ".py":
            cls_map, err = extract_code_symbols_from_python(fpath)
        else:
            cls_map, err = extract_code_symbols_from_polyglot(fpath)

        if err:
            parse_errors.append(err)
            continue

        for cls_name, methods in cls_map.items():
            implemented_classes.setdefault(cls_name, set()).update(methods)

    return implemented_classes, scanned_files, parse_errors


def parse_structured_pivots(pivots_text: str) -> Tuple[Set[str], Set[str]]:
    """
    Extracts structured pivot authorizations from YAML blocks (```yaml ... ```)
    or YAML frontmatter inside a pivots markdown document.
    Enforces rigid schema: only dictionary entries under `pivots:` containing
    `authorized_by: "human"` (case-insensitive) are accepted [IMP-ASI06-01].
    Extracts:
    - symbol: set of class/method/exception names
    - file: set of exact relative file paths (normalized with forward slashes)
    """
    pivoted_symbols: Set[str] = set()
    pivoted_files: Set[str] = set()
    if not pivots_text:
        return pivoted_symbols, pivoted_files

    yaml_blocks: List[str] = []
    # Frontmatter YAML
    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---", pivots_text, re.DOTALL)
    if fm_match:
        yaml_blocks.append(fm_match.group(1))

    # Fenced YAML blocks
    yaml_blocks.extend(re.findall(r"```ya?ml\r?\n(.*?)```", pivots_text, re.DOTALL))

    for block in yaml_blocks:
        try:
            data = yaml.safe_load(block)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        pivots_list = data.get("pivots", [])
        if not isinstance(pivots_list, list):
            continue
        for entry in pivots_list:
            if not isinstance(entry, dict):
                continue
            # Mandatory human authorization check (case-insensitive) [IMP-ASI06-01]
            auth_by = str(entry.get("authorized_by", "")).strip().lower()
            if auth_by != "human":
                continue

            sym = entry.get("symbol")
            if sym:
                pivoted_symbols.add(str(sym).strip())

            f_entry = entry.get("file")
            if f_entry:
                clean_f = str(f_entry).strip().replace("\\", "/")
                while clean_f.startswith("./"):
                    clean_f = clean_f[2:]
                pivoted_files.add(clean_f)

    return pivoted_symbols, pivoted_files



def check_drift(
    sdd_path: Path,
    targets: List[Path],
    pivots_path: Optional[Path] = None,
    batch_mode: bool = False,
    check_files: bool = False,
) -> Tuple[List[DriftFinding], List[str]]:
    """
    Compares SDD contracts against implemented code in targets.
    Returns (findings, errors).
    - If batch_mode=True, only verifies methods on classes already present in targets
      (does not fail on classes belonging to future batches).
    - If pivots_path is provided and exists, any symbol or exact file path authorized in the
      pivots document is marked as `authorized_by_pivot=True`.
    """
    errors: List[str] = []
    findings: List[DriftFinding] = []

    if not sdd_path.exists():
        return findings, [f"SDD file does not exist: {sdd_path}"]

    for t in targets:
        if not t.exists():
            errors.append(f"Target path does not exist: {t}")
    if errors:
        return findings, errors

    spec = extract_sdd_spec(sdd_path)
    implemented_classes, scanned_files, parse_errors = collect_implemented_symbols(targets)
    errors.extend(parse_errors)

    pivots_text = ""
    if pivots_path and pivots_path.exists():
        pivots_text = pivots_path.read_text(encoding="utf-8", errors="replace")

    structured_symbols, structured_files = parse_structured_pivots(pivots_text)

    def is_in_pivots(token: str) -> bool:
        return token in structured_symbols

    # 1. Check Classes / Interfaces and their Public Methods
    for expected_cls, expected_methods in sorted(spec.classes_and_methods.items()):
        if expected_cls not in implemented_classes:
            if not batch_mode:
                findings.append(
                    DriftFinding(
                        category="MISSING_CLASS",
                        symbol=expected_cls,
                        details=f"Class/Interface '{expected_cls}' declared in SDD was not found in scanned code.",
                        authorized_by_pivot=is_in_pivots(expected_cls),
                    )
                )
            continue

        actual_methods = implemented_classes[expected_cls]
        for expected_method in sorted(expected_methods):
            if expected_method not in actual_methods:
                qualified_symbol = f"{expected_cls}.{expected_method}"
                pivoted = (
                    is_in_pivots(qualified_symbol)
                    or is_in_pivots(expected_method)
                    or is_in_pivots(expected_cls)
                )
                findings.append(
                    DriftFinding(
                        category="MISSING_METHOD",
                        symbol=qualified_symbol,
                        details=(
                            f"Method '{qualified_symbol}()' declared in SDD "
                            f"is missing from implemented class '{expected_cls}'."
                        ),
                        authorized_by_pivot=pivoted,
                    )
                )

    # 2. Check Declared Exceptions (in Full Gate mode)
    if not batch_mode:
        for expected_exc in sorted(spec.exceptions):
            if expected_exc not in implemented_classes:
                findings.append(
                    DriftFinding(
                        category="MISSING_EXCEPTION",
                        symbol=expected_exc,
                        details=f"Exception class '{expected_exc}' declared in SDD contracts was not found in scanned code.",
                        authorized_by_pivot=is_in_pivots(expected_exc),
                    )
                )

    # 3. Optional File Impact Analysis check
    if check_files and spec.planned_files:
        for fpath in scanned_files:
            norm_path = str(fpath).replace("\\", "/")
            # Skip test files when checking production File Impact Analysis
            if "/tests/" in f"/{norm_path}" or fpath.name.startswith("test_"):
                continue
            matched = any(
                norm_path.endswith(planned) or planned.endswith(norm_path)
                for planned in spec.planned_files
            )
            if not matched:
                clean_norm = norm_path.lstrip("./")
                pivoted = False
                for sf in structured_files:
                    clean_sf = sf.lstrip("./")
                    if clean_norm == clean_sf or clean_norm.endswith("/" + clean_sf) or clean_sf.endswith("/" + clean_norm):
                        pivoted = True
                        break
                findings.append(
                    DriftFinding(
                        category="UNPLANNED_FILE",
                        symbol=norm_path,
                        details=(
                            f"Modified/created file '{norm_path}' is not listed in the SDD "
                            f"File Impact Analysis table ({sorted(spec.planned_files)})."
                        ),
                        authorized_by_pivot=pivoted,
                    )
                )

    return findings, errors


def print_report(
    sdd_path: Path,
    findings: List[DriftFinding],
    errors: List[str],
    batch_mode: bool,
) -> int:
    mode_label = "BATCH SCOPE (--batch)" if batch_mode else "FULL EXIT GATE"
    print(f"\n{'=' * 80}")
    print(f"🧭 SDD 2.0 DRIFT GATE REPORT [{mode_label}]")
    print(f"{'=' * 80}")
    print(f"SDD Contract Source: {sdd_path}")

    unauthorized = [f for f in findings if not f.authorized_by_pivot]
    authorized = [f for f in findings if f.authorized_by_pivot]

    print(f"Unauthorized Spec Drifts: {len(unauthorized)}")
    print(f"Authorized Technical Pivots: {len(authorized)}")
    if errors:
        print(f"Execution/Parse Errors: {len(errors)}")
    print()

    if errors:
        print("⚠️  ERRORS:")
        for err in errors:
            print(f"   [!] {err}")
        print()

    if authorized:
        print("ℹ️  AUTHORIZED TECHNICAL PIVOTS (Documented in pivots-[slug].md):")
        for f in authorized:
            print(f"   [PIVOT] [{f.category}] {f.symbol} — {f.details}")
        print()

    if unauthorized:
        print("🔴 UNAUTHORIZED SPEC DRIFT DETECTED:")
        for f in unauthorized:
            print(f"   ❌ [{f.category}] {f.symbol}")
            print(f"      Details: {f.details}")
            print(
                "      Action:  Align code with SDD contract OR document an authorized Technical Pivot in "
                "02-auditorias/pivots-[slug].md (YAML schema with authorized_by: 'human') and update SDD."
            )
        print(f"{'=' * 80}\n")
        return 1

    if errors:
        print(f"{'=' * 80}\n")
        return 1

    print("✅ [PASS] Zero unauthorized specification drift detected between SDD and code.")
    print(f"{'=' * 80}\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SDD 2.0 Drift Gate Validator: Compares implemented code against SDD contracts."
    )
    parser.add_argument(
        "sdd_path",
        help="Path to SDD specification file (01-concepcao/sdd-[slug].md or .yaml)",
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help="Target source files or directories to verify (e.g. src/)",
    )
    parser.add_argument(
        "--pivots",
        dest="pivots_path",
        default=None,
        help="Optional path to Technical Pivots note (02-auditorias/pivots-[slug].md)",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch mode: only validate methods for classes already implemented in targets",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Also verify that target production files are listed in SDD File Impact Analysis",
    )
    parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit with code 0 (warning-only mode)",
    )

    args = parser.parse_args()
    sdd_file = Path(args.sdd_path)
    target_paths = [Path(t) for t in args.targets]
    pivots_file = Path(args.pivots_path) if args.pivots_path else None

    findings, errors = check_drift(
        sdd_path=sdd_file,
        targets=target_paths,
        pivots_path=pivots_file,
        batch_mode=args.batch,
        check_files=args.check_files,
    )

    exit_code = print_report(sdd_file, findings, errors, batch_mode=args.batch)
    if args.exit_zero:
        return 0
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
