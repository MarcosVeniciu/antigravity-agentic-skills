#!/usr/bin/env python3
"""
AST Complexity & Performance Anti-Pattern Scanner (Zero External Dependencies)
Used by workflows-skill/review to calculate Cyclomatic Complexity V(G) and detect Big-O heuristics in Python.
"""

import ast
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Iterator

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def iter_function_scope_nodes(node: ast.AST) -> Iterator[ast.AST]:
    """
    Yield all child AST nodes within the current function body,
    without descending into nested functions, lambdas, or class definitions.
    Prevents nested closure/helper complexity from polluting the parent function.
    """
    stack = list(ast.iter_child_nodes(node))
    while stack:
        curr = stack.pop()
        yield curr
        if not isinstance(curr, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            stack.extend(ast.iter_child_nodes(curr))


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self, filename: str, threshold: int = 10):
        self.filename = filename
        self.threshold = threshold
        self.high_complexity_functions: List[Dict[str, Any]] = []
        self.heuristic_warnings: List[Dict[str, Any]] = []
        self._loop_depth = 0

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._analyze_function(node)
        self.generic_visit(node)

    def _analyze_function(self, node):
        complexity = 1  # Base complexity (McCabe metric)
        
        for child in iter_function_scope_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.IfExp):  # Ternary operator: x if cond else y
                complexity += 1
            elif isinstance(child, ast.BoolOp):  # 'and' / 'or'
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                for comp in child.generators:
                    complexity += 1 + len(comp.ifs)
            elif hasattr(ast, "match_case") and isinstance(child, ast.match_case):
                complexity += 1

        if complexity > self.threshold:
            self.high_complexity_functions.append({
                "file": self.filename,
                "name": node.name,
                "line": node.lineno,
                "complexity": complexity
            })

    def visit_For(self, node: ast.For):
        self._check_loop(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self._check_loop(node)

    def visit_While(self, node: ast.While):
        self._check_loop(node)

    def _check_loop(self, node):
        self._loop_depth += 1
        
        # Check for nested loops -> O(n^2) or higher
        if self._loop_depth >= 2:
            self.heuristic_warnings.append({
                "file": self.filename,
                "line": node.lineno,
                "type": "O(n^2) Nested Loop",
                "message": f"Nested loop detected at depth {self._loop_depth}. Check asymptotic complexity bounds."
            })
            
        # Check for linear search inside loop -> O(n*m) without traversing nested functions
        for child in iter_function_scope_nodes(node):
            if isinstance(child, ast.Compare):
                for op in child.ops:
                    if isinstance(op, (ast.In, ast.NotIn)):
                        self.heuristic_warnings.append({
                            "file": self.filename,
                            "line": child.lineno,
                            "type": "Linear Search in Loop",
                            "message": "Found 'in' lookup inside a loop. If target is a list/tuple, complexity may be O(n*m). Consider converting to set/dict."
                        })

        self.generic_visit(node)
        self._loop_depth -= 1


def scan_file(filepath: Path, threshold: int) -> Dict[str, Any]:
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(content, filename=str(filepath))
        visitor = ComplexityVisitor(str(filepath), threshold=threshold)
        visitor.visit(tree)
        return {
            "high_complexity": visitor.high_complexity_functions,
            "warnings": visitor.heuristic_warnings
        }
    except Exception as e:
        return {
            "error": f"Failed to parse {filepath}: {str(e)}",
            "high_complexity": [],
            "warnings": []
        }


def main():
    parser = argparse.ArgumentParser(description="AST Cyclomatic Complexity and Asymptotic Heuristic Scanner")
    parser.add_argument("targets", nargs="+", help="Files or directories to scan (.py)")
    parser.add_argument("--threshold", type=int, default=10, help="Cyclomatic complexity threshold (default: 10)")
    parser.add_argument("--exit-zero", action="store_true", help="Always exit with 0 (non-blocking mode)")
    args = parser.parse_args()

    files_to_scan: List[Path] = []
    files_not_found: List[str] = []
    unsupported_files: List[str] = []

    for target in args.targets:
        target_path = Path(target)
        if not target_path.exists():
            files_not_found.append(target)
            continue

        if target_path.is_file():
            if target_path.suffix == ".py":
                files_to_scan.append(target_path)
            else:
                unsupported_files.append(str(target_path))
        elif target_path.is_dir():
            files_to_scan.extend(target_path.glob("**/*.py"))

    all_high_complexity: List[Dict[str, Any]] = []
    all_warnings: List[Dict[str, Any]] = []
    files_with_errors: List[str] = []

    for filepath in files_to_scan:
        result = scan_file(filepath, args.threshold)
        if "error" in result:
            files_with_errors.append(result["error"])
        else:
            all_high_complexity.extend(result["high_complexity"])
            all_warnings.extend(result["warnings"])

    print("\n" + "=" * 80)
    print("🧹 AUDIT REPORT: PYTHON AST COMPLEXITY & PERFORMANCE HEURISTICS")
    print("=" * 80)
    print(f"Python files analyzed: {len(files_to_scan)}")
    if unsupported_files:
        print(f"Non-Python files skipped (evaluated manually / native linters): {len(unsupported_files)}")
    if files_not_found:
        print(f"Targets not found: {len(files_not_found)}")
    if files_with_errors:
        print(f"Files with parse errors: {len(files_with_errors)}")
    print()

    if files_not_found:
        print("⚠️  MISSING TARGETS:")
        for nf in files_not_found:
            print(f"   [!] Target does not exist: {nf}")
        print()

    if files_with_errors:
        print("⚠️  PARSING ERRORS:")
        for err in files_with_errors:
            print(f"   [!] {err}")
        print()

    if all_high_complexity:
        print(f"🔴 HIGH CYCLOMATIC COMPLEXITY V(G) > {args.threshold}:")
        for fn in all_high_complexity:
            print(f"   * {fn['file']}:{fn['line']} - Function '{fn['name']}' has V(G) = {fn['complexity']}")
        print()
    else:
        print(f"✅ [OK] Cyclomatic complexity V(G) within limits (<= {args.threshold}) for all analyzed functions.")

    if all_warnings:
        print("\n🟡 ASYMPTOTIC HEURISTIC WARNINGS (Potential Algorithmic Bottlenecks):")
        for w in all_warnings:
            print(f"   * {w['file']}:{w['line']} [{w['type']}] {w['message']}")
    else:
        print("✅ [OK] No nested loops or linear searches in loops detected.")

    print("=" * 80 + "\n")

    has_blocking_issues = (
        len(all_high_complexity) > 0
        or len(files_with_errors) > 0
        or len(files_not_found) > 0
    )

    if args.exit_zero:
        sys.exit(0)
    sys.exit(1 if has_blocking_issues else 0)


if __name__ == "__main__":
    main()
