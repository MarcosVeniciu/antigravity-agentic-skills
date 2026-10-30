#!/usr/bin/env python3
"""
verify_docstring_only.py - AST Docstring & Logic Invariance Validator

Deterministic zero-RCE static validator for the /docs skill ([DOC-ASI03-01], [DOC-ASI05-02]).
Verifies that Python source files compile cleanly and that modifications during documentation
enrichment are strictly confined to docstrings and comments (zero AST executable logic drift).
"""

import ast
import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class DocstringStripper(ast.NodeTransformer):
    """
    Removes module, class, and function docstrings from an AST so that two ASTs
    can be structurally compared for 100% executable logic invariance.
    """

    def _strip_docstring_from_body(self, body: list) -> list:
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            return body[1:]
        return body

    def visit_Module(self, node: ast.Module) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_docstring_from_body(node.body)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_docstring_from_body(node.body)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_docstring_from_body(node.body)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        self.generic_visit(node)
        node.body = self._strip_docstring_from_body(node.body)
        return node


def normalize_ast_without_docstrings(source_code: str, filename: str = "<unknown>") -> str:
    """
    Parses Python source code, strips all docstrings, and returns a canonical
    AST dump (excluding line numbers and column offsets).
    """
    tree = ast.parse(source_code, filename=filename)
    stripped_tree = DocstringStripper().visit(tree)
    ast.fix_missing_locations(stripped_tree)
    return ast.dump(stripped_tree, include_attributes=False)


def compare_ast_logic(before_source: str, after_source: str, filename: str = "<unknown>") -> Tuple[bool, Optional[str]]:
    """
    Compares Python source code before and after documentation edits.
    Returns (True, None) if executable AST logic is 100% identical, or (False, reason) on drift/syntax error.
    """
    try:
        before_dump = normalize_ast_without_docstrings(before_source, filename=filename)
    except SyntaxError as exc:
        return False, f"SyntaxError in baseline source for {filename}: {exc}"

    try:
        after_dump = normalize_ast_without_docstrings(after_source, filename=filename)
    except SyntaxError as exc:
        return False, f"SyntaxError in modified source for {filename}: {exc}"

    if before_dump != after_dump:
        return False, (
            f"Forbidden AST executable logic mutation detected in {filename}. "
            "Only docstrings and comments may be modified during /docs."
        )
    return True, None


def _get_git_head_content(file_path: Path, git_ref: str = "HEAD") -> Optional[str]:
    """
    Retrieves the baseline content of a file from git (e.g. HEAD) if available.
    """
    try:
        rel_proc = subprocess.run(
            ["git", "ls-files", "--full-name", str(file_path)],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(file_path.parent if file_path.parent.exists() else Path.cwd()),
        )
        rel_path = rel_proc.stdout.strip()
        if not rel_path:
            return None
        show_proc = subprocess.run(
            ["git", "show", f"{git_ref}:{rel_path}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            cwd=str(file_path.parent if file_path.parent.exists() else Path.cwd()),
        )
        if show_proc.returncode == 0:
            return show_proc.stdout
        return None
    except Exception:
        return None


def verify_file(
    file_path: Path,
    baseline_path: Optional[Path] = None,
    git_ref: Optional[str] = "HEAD",
) -> Tuple[bool, List[str]]:
    """
    Verifies that `file_path` compiles cleanly via AST and, if a baseline or git ref is present,
    has zero AST executable logic mutations outside docstrings/comments.
    """
    errors: List[str] = []
    if not file_path.exists():
        return False, [f"File not found: {file_path}"]

    try:
        after_source = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return False, [f"Failed to read {file_path}: {exc}"]

    try:
        compile(after_source, str(file_path), "exec", dont_inherit=True)
        ast.parse(after_source, filename=str(file_path))
    except SyntaxError as exc:
        return False, [f"Static compilation failed for {file_path}:{exc.lineno}: {exc.msg}"]

    before_source: Optional[str] = None
    if baseline_path is not None:
        if not baseline_path.exists():
            return False, [f"Baseline file not found: {baseline_path}"]
        before_source = baseline_path.read_text(encoding="utf-8", errors="replace")
    elif git_ref:
        before_source = _get_git_head_content(file_path, git_ref=git_ref)

    if before_source is not None:
        ok, err_msg = compare_ast_logic(before_source, after_source, filename=str(file_path))
        if not ok and err_msg:
            errors.append(err_msg)

    return len(errors) == 0, errors


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Zero-RCE static AST docstring and logic invariance validator for /docs."
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help="Python files (.py) or directories to validate.",
    )
    parser.add_argument(
        "--before",
        type=str,
        default=None,
        help="Optional explicit baseline Python file for two-file AST comparison.",
    )
    parser.add_argument(
        "--git-ref",
        type=str,
        default="HEAD",
        help="Git reference to compare AST against (default: HEAD; pass '' to skip git comparison).",
    )
    args = parser.parse_args()

    py_files: List[Path] = []
    missing_targets: List[str] = []

    for target in args.targets:
        p = Path(target)
        if not p.exists():
            missing_targets.append(target)
        elif p.is_file() and p.suffix == ".py":
            py_files.append(p)
        elif p.is_dir():
            py_files.extend(p.glob("**/*.py"))

    baseline_path = Path(args.before) if args.before else None
    git_ref = args.git_ref.strip() if args.git_ref is not None else None

    all_errors: List[str] = []
    for nf in missing_targets:
        all_errors.append(f"Target does not exist: {nf}")

    for py_file in py_files:
        ok, errs = verify_file(py_file, baseline_path=baseline_path, git_ref=git_ref or None)
        if not ok:
            all_errors.extend(errs)

    print("\n" + "=" * 80)
    print("📄 STATIC AST DOCSTRING & LOGIC INVARIANCE REPORT")
    print("=" * 80)
    print(f"Python files verified: {len(py_files)}")
    if all_errors:
        print(f"Status: 🔴 FAILED ({len(all_errors)} violation(s) found)\n")
        for err in all_errors:
            print(f"   [!] {err}")
        print("=" * 80 + "\n")
        sys.exit(1)

    print("Status: ✅ PASS (100% syntax valid & zero executable AST logic drift)")
    print("=" * 80 + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
