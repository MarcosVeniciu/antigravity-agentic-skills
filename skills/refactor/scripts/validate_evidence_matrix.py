#!/usr/bin/env python3
"""
skills/refactor/scripts/validate_evidence_matrix.py
Programmatic Refactoring Evidence Matrix Validator (Zero External Dependencies).

Enforces:
1. Extraction of the Evidence Matrix table from 02-auditorias/refactor-[slug].md.
2. AST-based recalculation of actual cyclomatic complexity V(G) for every reported target function.
3. Verification that:
   - V(G)_actual <= threshold (default: 10).
   - V(G)_actual == V(G)_after_reported (rejects hallucinated or complacency metrics).
   - Exit code 1 on any discrepancy or threshold violation.
"""

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def iter_function_scope_nodes(node: ast.AST) -> Iterator[ast.AST]:
    """Yields all child AST nodes in function scope without entering nested scopes."""
    stack = list(ast.iter_child_nodes(node))
    while stack:
        curr = stack.pop()
        yield curr
        if not isinstance(curr, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            stack.extend(ast.iter_child_nodes(curr))


def calculate_function_complexity(node: ast.AST) -> int:
    """Calculates McCabe Cyclomatic Complexity V(G) for an individual function AST node."""
    complexity = 1
    for child in iter_function_scope_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.IfExp):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for comp in child.generators:
                complexity += 1 + len(comp.ifs)
        elif hasattr(ast, "match_case") and isinstance(child, ast.match_case):
            complexity += 1
    return complexity


def extract_file_complexities(content: str, filename: str = "<string>") -> Dict[str, Dict[str, Any]]:
    """Returns mapping of function names to their line number and actual V(G)."""
    try:
        tree = ast.parse(content, filename=filename)
    except SyntaxError as e:
        return {}

    complexities: Dict[str, Dict[str, Any]] = {}

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            complexities[node.name] = {
                "line": node.lineno,
                "complexity": calculate_function_complexity(node),
            }
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            complexities[node.name] = {
                "line": node.lineno,
                "complexity": calculate_function_complexity(node),
            }
            self.generic_visit(node)

    Visitor().visit(tree)
    return complexities


def parse_evidence_matrix_table(markdown_text: str) -> List[Dict[str, Any]]:
    """
    Parses Markdown tables looking for Evidence Matrix rows containing:
    Target / Function / Method, V(G) Before, V(G) After, Status.
    """
    entries: List[Dict[str, Any]] = []
    lines = markdown_text.splitlines()
    in_matrix_table = False

    for line in lines:
        line_clean = line.strip()
        if not line_clean.startswith("|") or not line_clean.endswith("|"):
            in_matrix_table = False
            continue

        cells = [c.strip() for c in line_clean.strip("|").split("|")]
        lower_cells = [c.lower() for c in cells]

        # Detect header row
        if any("target" in c or "function" in c or "método" in c for c in lower_cells) and any(
            "v(g)" in c or "complexity" in c or "complexidade" in c for c in lower_cells
        ):
            in_matrix_table = True
            continue

        if in_matrix_table:
            # Skip separator line (e.g. |---|---|)
            if all(re.match(r"^:?-+:?$", c) for c in cells if c):
                continue

            if len(cells) >= 3:
                target_name = cells[0].strip("`* ")
                # Find before and after numbers in subsequent cells
                numbers = []
                for cell in cells[1:]:
                    nums = re.findall(r"\b\d+\b", cell)
                    if nums:
                        numbers.append(int(nums[0]))

                if len(numbers) >= 2:
                    entries.append({
                        "name": target_name,
                        "vg_before": numbers[0],
                        "vg_after": numbers[1],
                        "raw_cells": cells,
                    })
                elif len(numbers) == 1:
                    entries.append({
                        "name": target_name,
                        "vg_before": None,
                        "vg_after": numbers[0],
                        "raw_cells": cells,
                    })

    return entries


def validate_evidence_matrix(
    report_content: str,
    source_files: Dict[str, str],
    threshold: int = 10,
) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
    """
    Validates evidence matrix entries against actual AST complexities of source files.
    """
    errors: List[str] = []
    verified_entries: List[Dict[str, Any]] = []

    matrix_entries = parse_evidence_matrix_table(report_content)
    if not matrix_entries:
        return False, ["Evidence Matrix validation failed: No table rows with V(G) metrics found in report."], []

    # Map all functions across source files
    all_actual_complexities: Dict[str, Dict[str, Any]] = {}
    for filename, content in source_files.items():
        file_complexities = extract_file_complexities(content, filename=filename)
        for fn_name, info in file_complexities.items():
            all_actual_complexities[fn_name] = {**info, "file": filename}

    for entry in matrix_entries:
        fn_name = entry["name"]
        reported_after = entry["vg_after"]

        # Check if function exists in source files
        if fn_name not in all_actual_complexities:
            # Also check if target was class.method
            short_name = fn_name.split(".")[-1]
            if short_name in all_actual_complexities:
                actual_info = all_actual_complexities[short_name]
            else:
                errors.append(
                    f"[UNRESOLVED_FUNCTION] Target '{fn_name}' from Evidence Matrix not found in modified source files."
                )
                continue
        else:
            actual_info = all_actual_complexities[fn_name]

        actual_vg = actual_info["complexity"]
        entry["vg_actual"] = actual_vg
        entry["file"] = actual_info["file"]
        entry["line"] = actual_info["line"]

        # Validate V(G) <= threshold
        if actual_vg > threshold:
            errors.append(
                f"[COMPLEXITY_VIOLATION] '{fn_name}' has actual V(G)={actual_vg} > {threshold} (line {actual_info['line']} in {actual_info['file']})."
            )

        # Validate V(G)_actual == V(G)_after_reported
        if reported_after is not None and actual_vg != reported_after:
            errors.append(
                f"[METRIC_DISCREPANCY] '{fn_name}': reported V(G) after={reported_after}, but actual AST V(G)={actual_vg}."
            )

        verified_entries.append(entry)

    is_ok = len(errors) == 0
    return is_ok, errors, verified_entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Programmatic Refactoring Evidence Matrix Validator")
    parser.add_argument("report", help="Path to refactoring report (e.g. 02-auditorias/refactor-[slug].md)")
    parser.add_argument("sources", nargs="*", help="Paths to modified Python source files to verify")
    parser.add_argument("--threshold", type=int, default=10, help="Maximum allowed V(G) (default: 10)")
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"❌ Report file not found: '{report_path}'")
        return 1

    report_content = report_path.read_text(encoding="utf-8", errors="replace")

    source_files: Dict[str, str] = {}
    source_paths = [Path(p) for p in args.sources]
    if not source_paths:
        # Default scan src/ directory
        src_dir = Path("src")
        if src_dir.exists():
            source_paths = list(src_dir.rglob("*.py"))

    for p in source_paths:
        if p.exists() and p.suffix == ".py":
            source_files[str(p).replace("\\", "/")] = p.read_text(encoding="utf-8", errors="replace")

    ok, errors, verified = validate_evidence_matrix(report_content, source_files, threshold=args.threshold)

    print("======================================================================")
    print("      Refactoring Evidence Matrix Programmatic Validation")
    print("======================================================================")
    for v in verified:
        status_icon = "✅" if v.get("vg_actual", 99) <= args.threshold else "❌"
        print(f" {status_icon} {v['name']}: Before={v.get('vg_before', '?')} -> Reported={v['vg_after']} -> Actual AST={v.get('vg_actual', '?')} ({v.get('file', '')}:{v.get('line', '')})")

    if not ok:
        print("\n❌ Evidence Matrix Validation FAILED:")
        for err in errors:
            print(f"   - {err}")
        return 1

    print(f"\n✅ Evidence Matrix Validation PASSED! All {len(verified)} function(s) verified against real AST.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

