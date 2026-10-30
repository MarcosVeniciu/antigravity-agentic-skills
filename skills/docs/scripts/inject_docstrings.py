#!/usr/bin/env python3
"""
inject_docstrings.py - AST Deterministic Docstring Injector & Obsidian Traceability Linker

Part of the /docs skill in SDD 2.0 (EV-DOC-01, [DOC-ASI03-01], [DOC-ASI09-03]).
Deterministically enriches Python source files with BDD/SDD Obsidian traceability links
without requiring LLM/subagent direct write privileges over production code (.py).

Enforces the Public Schema Exception ([DOC-ASI09-03]):
FastAPI routes (@app.get, @router.post), Pydantic models (BaseModel), and Typer/Click CLI
commands are protected from receiving internal Obsidian wikilinks ([[...]]) to prevent
internal metadata leakage into public OpenAPI/Swagger schemas and CLI --help outputs.
"""

import argparse
import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def is_pydantic_model(node: ast.ClassDef) -> bool:
    """Checks if a ClassDef inherits from BaseModel or BaseSettings."""
    for base in node.bases:
        try:
            base_repr = ast.unparse(base)
        except Exception:
            base_repr = ""
        if (
            base_repr == "BaseModel"
            or base_repr.endswith(".BaseModel")
            or base_repr == "BaseSettings"
            or base_repr.endswith(".BaseSettings")
        ):
            return True
    return False


def has_public_schema_decorator(node: ast.AST) -> bool:
    """
    Checks if a function has decorators matching framework endpoints or CLI commands:
    - FastAPI / Starlette / Flask: @app.get, @router.post, @api_router.put, @bp.route, etc.
    - Click: @click.command, @click.group, @cli.command
    - Typer: @app.command
    """
    endpoint_methods = {"get", "post", "put", "delete", "patch", "options", "head", "route", "websocket"}
    endpoint_objects = {"app", "router", "api_router", "api", "bp", "blueprint", "v1_router"}
    cli_objects = {"click", "cli", "typer"}
    cli_methods = {"command", "group"}

    for dec in getattr(node, "decorator_list", []):
        target = dec.func if isinstance(dec, ast.Call) else dec
        try:
            dec_str = ast.unparse(target)
        except Exception:
            continue

        parts = dec_str.split(".")
        if len(parts) >= 2:
            obj_name = parts[-2]
            method_name = parts[-1]
            if (obj_name in endpoint_objects or "router" in obj_name.lower()) and method_name in endpoint_methods:
                return True
            if obj_name in cli_objects and method_name in cli_methods:
                return True
            if method_name in {"command", "group"} and any(k in dec_str.lower() for k in ["app", "cli", "click", "typer"]):
                return True

        # Fallback prefix/suffix checks
        if any(dec_str.startswith(f"{prefix}.") for prefix in ["click", "typer"]):
            return True
        for m in endpoint_methods:
            if dec_str.endswith(f".{m}") and any(obj in dec_str for obj in ["app", "router", "bp", "api"]):
                return True

    return False


def is_public_schema(node: ast.AST, parent_classes: Optional[List[ast.ClassDef]] = None) -> bool:
    """
    Checks if a node is subject to the Public Schema Exception ([DOC-ASI09-03]).
    Public endpoints, Pydantic models, or CLI entrypoints must NOT have internal
    Obsidian wikilinks injected into their docstrings.
    """
    if parent_classes:
        for p in parent_classes:
            if is_pydantic_model(p):
                return True

    if isinstance(node, ast.ClassDef):
        return is_pydantic_model(node)

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return has_public_schema_decorator(node)

    return False


class TargetCollector(ast.NodeVisitor):
    """Collects all ClassDef, FunctionDef, and AsyncFunctionDef nodes with their class hierarchy."""

    def __init__(self):
        self.class_stack: List[ast.ClassDef] = []
        self.targets: List[Tuple[ast.AST, List[ast.ClassDef]]] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        self.targets.append((node, list(self.class_stack)))
        self.class_stack.append(node)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.targets.append((node, list(self.class_stack)))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.targets.append((node, list(self.class_stack)))
        self.generic_visit(node)


def find_header_end(lines: List[str], start_lineno: int, first_body_lineno: int) -> int:
    """
    Finds the 0-based line index where the def or class signature header ends
    (the line terminating with ':' before the body statements start).
    """
    if first_body_lineno == start_lineno:
        return start_lineno - 1

    last_colon_idx = start_lineno - 1
    for idx in range(start_lineno - 1, min(first_body_lineno - 1, len(lines))):
        code_part = lines[idx].split("#")[0].rstrip()
        if code_part.endswith(":"):
            last_colon_idx = idx
    return last_colon_idx


def detect_line_ending(content: str) -> str:
    """Detects whether the file uses CRLF or LF line endings."""
    return "\r\n" if "\r\n" in content else "\n"


def get_indentation(lines: List[str], node: ast.AST, first_body: ast.AST) -> str:
    """Determines original indentation string for inserting a docstring."""
    if first_body.lineno > node.lineno and first_body.lineno <= len(lines):
        body_line = lines[first_body.lineno - 1]
        indent = body_line[: len(body_line) - len(body_line.lstrip())]
        if indent:
            return indent
    # Fallback based on node line
    if node.lineno <= len(lines):
        node_line = lines[node.lineno - 1]
        base_indent = node_line[: len(node_line) - len(node_line.lstrip())]
        return base_indent + "    "
    return "    "


def enrich_existing_docstring(raw_doc_literal: str, sdd_slug: str, col_offset: int) -> str:
    """
    Enriches an existing docstring literal by appending the Obsidian traceability reference
    while preserving existing content and quotes.
    """
    clean_slug = sdd_slug.removeprefix("sdd-")
    wikilink = f"[[sdd-{clean_slug}]]"

    if wikilink in raw_doc_literal or "Ref: Obsidian note [[sdd-" in raw_doc_literal:
        return raw_doc_literal

    # Detect closing quote style
    if raw_doc_literal.endswith('"""'):
        quote = '"""'
    elif raw_doc_literal.endswith("'''"):
        quote = "'''"
    elif raw_doc_literal.endswith('"'):
        quote = '"'
    elif raw_doc_literal.endswith("'"):
        quote = "'"
    else:
        quote = '"""'

    body = raw_doc_literal[:-len(quote)]

    # If empty docstring (e.g. """""")
    if body == quote or body == quote.lstrip("rRuUbB"):
        return f'{quote}Ref: Obsidian note [[sdd-{clean_slug}]]{quote}'

    indent_str = " " * col_offset
    if "\n" in raw_doc_literal:
        # Multiline docstring
        return f"{body.rstrip()}\n\n{indent_str}Ref: Obsidian note [[sdd-{clean_slug}]]\n{indent_str}{quote}"
    else:
        # Single-line docstring
        return f"{body.rstrip()} Ref: Obsidian note [[sdd-{clean_slug}]]{quote}"


def inject_docstrings_in_source(source: str, sdd_slug: str, filename: str = "<unknown>") -> Tuple[str, int, int]:
    """
    Parses Python source code, inspects classes and functions via AST, and deterministically
    injects or enriches docstrings with Obsidian traceability references.

    Returns:
        (modified_source, added_count, enriched_count)
    """
    clean_slug = sdd_slug.removeprefix("sdd-")
    tree = ast.parse(source, filename=filename)

    line_ending = detect_line_ending(source)
    lines = source.splitlines(keepends=True)
    if not lines:
        return source, 0, 0

    collector = TargetCollector()
    collector.visit(tree)

    # Filter targets and classify into existing vs new docstring modifications
    modifications = []
    added_count = 0
    enriched_count = 0

    for node, parent_classes in collector.targets:
        if is_public_schema(node, parent_classes):
            # [DOC-ASI09-03] Public Schema Exception: omit Obsidian wikilinks
            continue

        if not hasattr(node, "body") or not node.body:
            continue

        first_body = node.body[0]
        has_doc = (
            isinstance(first_body, ast.Expr)
            and isinstance(first_body.value, ast.Constant)
            and isinstance(first_body.value.value, str)
        )

        if has_doc:
            doc_str = first_body.value.value
            if f"[[sdd-{clean_slug}]]" in doc_str or "Ref: Obsidian note [[sdd-" in doc_str:
                continue

            modifications.append({
                "type": "ENRICH",
                "start_line": first_body.lineno,
                "end_line": first_body.end_lineno,
                "start_col": first_body.col_offset,
                "end_col": first_body.end_col_offset,
                "col_offset": first_body.col_offset,
                "sort_key": first_body.lineno,
            })
        else:
            modifications.append({
                "type": "NEW",
                "node": node,
                "first_body": first_body,
                "sort_key": node.lineno,
            })

    # Sort modifications from bottom to top (highest line number first)
    modifications.sort(key=lambda m: m["sort_key"], reverse=True)

    for mod in modifications:
        if mod["type"] == "ENRICH":
            start_l = mod["start_line"]
            end_l = mod["end_line"]
            start_c = mod["start_col"]
            end_c = mod["end_col"]

            if start_l == end_l:
                line_idx = start_l - 1
                raw_doc = lines[line_idx][start_c:end_c]
                new_doc = enrich_existing_docstring(raw_doc, clean_slug, mod["col_offset"])
                if new_doc != raw_doc:
                    lines[line_idx] = lines[line_idx][:start_c] + new_doc + lines[line_idx][end_c:]
                    enriched_count += 1
            else:
                prefix = lines[start_l - 1][:start_c]
                suffix = lines[end_l - 1][end_c:]
                first_part = lines[start_l - 1][start_c:]
                mid_part = "".join(lines[start_l : end_l - 1])
                last_part = lines[end_l - 1][:end_c]
                raw_doc = first_part + mid_part + last_part

                new_doc = enrich_existing_docstring(raw_doc, clean_slug, mod["col_offset"])
                if new_doc != raw_doc:
                    lines[start_l - 1 : end_l] = [prefix + new_doc + suffix]
                    enriched_count += 1

        elif mod["type"] == "NEW":
            node = mod["node"]
            first_body = mod["first_body"]
            header_idx = find_header_end(lines, node.lineno, first_body.lineno)
            indent = get_indentation(lines, node, first_body)

            new_doc_line = f'{indent}"""Ref: Obsidian note [[sdd-{clean_slug}]]"""{line_ending}'

            if first_body.lineno == node.lineno:
                # Single-line definition: def foo(): pass
                line_content = lines[header_idx]
                if ":" in line_content:
                    head, tail = line_content.split(":", 1)
                    lines[header_idx] = (
                        f"{head}:{line_ending}"
                        f"{new_doc_line}"
                        f"{indent}{tail.strip()}{line_ending}"
                    )
                    added_count += 1
            else:
                lines.insert(header_idx + 1, new_doc_line)
                added_count += 1

    return "".join(lines), added_count, enriched_count


def process_file(
    file_path: Path, sdd_slug: str, dry_run: bool = False
) -> Tuple[bool, int, int, Optional[str]]:
    """
    Processes a single Python file, injecting docstrings deterministically.

    Returns:
        (changed, added_count, enriched_count, error_message)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        return False, 0, 0, f"Failed to read {file_path}: {exc}"

    try:
        modified_content, added, enriched = inject_docstrings_in_source(
            content, sdd_slug, filename=str(file_path)
        )
    except SyntaxError as exc:
        return False, 0, 0, f"SyntaxError in {file_path}: {exc}"
    except Exception as exc:
        return False, 0, 0, f"Error processing {file_path}: {exc}"

    changed = modified_content != content
    if changed and not dry_run:
        try:
            file_path.write_text(modified_content, encoding="utf-8")
        except Exception as exc:
            return False, 0, 0, f"Failed to write {file_path}: {exc}"

    return changed, added, enriched, None


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="AST Deterministic Docstring Injector & Obsidian Traceability Linker"
    )
    parser.add_argument("files", nargs="+", help="Python source files to inspect and enrich")
    parser.add_argument(
        "--sdd-slug",
        required=True,
        help="SDD specification slug identifier (e.g. payment-gateway)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate modifications without writing to disk",
    )

    args = parser.parse_args(argv)

    total_added = 0
    total_enriched = 0
    has_errors = False

    for file_str in args.files:
        path = Path(file_str).resolve()
        if not path.is_file():
            print(f"⚠️  [SKIP] File not found: {file_str}", file=sys.stderr)
            continue
        if path.suffix != ".py":
            print(f"⚠️  [SKIP] Non-python file ignored: {file_str}")
            continue

        changed, added, enriched, err = process_file(path, args.sdd_slug, dry_run=args.dry_run)
        if err:
            print(f"❌ [ERROR] {file_str}: {err}", file=sys.stderr)
            has_errors = True
            continue

        total_added += added
        total_enriched += enriched

        status = "[DRY-RUN]" if args.dry_run else "[INJECTED]"
        if changed:
            print(f"✅ {status} {file_str}: {added} docstrings inserted, {enriched} enriched")
        else:
            print(f"ℹ️  [UNCHANGED] {file_str}: all docstrings up to date")

    if has_errors:
        return 1

    print(
        f"\n🎯 [SUMMARY] Completed: {total_added} docstrings added, {total_enriched} enriched."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
