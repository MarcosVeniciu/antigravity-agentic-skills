#!/usr/bin/env python3
"""
skills/decompose/scripts/validate_dag.py
Deterministic Directed Acyclic Graph (DAG) and Evolutionary Slicing Validator for Phase 0 (/decompose).

Enforces:
1. Extraction of task dependencies from the Markdown Task Inventory table
   and/or Mermaid `flowchart TD` / `graph TD` blocks.
2. Deterministic cycle detection via Python stdlib `graphlib.TopologicalSorter` (`CycleError`).
3. Strict sizing calibration: every task's Size must be `[S]`, `[M]`, or `[SPIKE]`;
   monolithic `[L]` or `[XL]` slices are strictly rejected with exit code 1.
4. Contract topological order verification: any contract listed in `Contracts Consumed`
   (if also introduced in the epic) must be introduced by an ancestor/dependency task
   before it is consumed.
5. Strict slug sanitization (`^[a-z0-9]+(-[a-z0-9]+)*$`) for `--slug`, frontmatter `epic_slug`,
   and branch recommendations to prevent shell metacharacter injection.
6. UTF-8 console encoding safety on Windows (cp1252 fix).
"""

import argparse
import graphlib
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SLUG_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ALLOWED_SIZES = {"[S]", "[M]", "[SPIKE]"}
FORBIDDEN_SIZES = {"[L]", "[XL]"}
NONE_VALUES = {"—", "-", "none", "n/a", "null", ""}


def validate_slug(slug: str, context: str = "slug") -> Optional[str]:
    """Validates that a slug strictly matches ^[a-z0-9]+(-[a-z0-9]+)*$."""
    clean = slug.strip()
    if "{{" in clean and "}}" in clean:
        return None
    if not SLUG_REGEX.match(clean):
        return (
            f"Invalid {context} '{clean}': must strictly match regex "
            f"'^[a-z0-9]+(-[a-z0-9]+)*$' (lowercase alphanumeric and single hyphens only)."
        )
    return None


def extract_slugs_from_content(content: str) -> List[Tuple[str, str]]:
    """Extracts epic_slug from YAML frontmatter and branch slugs from checkout commands."""
    extracted: List[Tuple[str, str]] = []
    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        slug_match = re.search(
            r"^epic_slug\s*:\s*['\"]?([^'\"\r\n]+)['\"]?", fm_text, re.MULTILINE
        )
        if slug_match:
            val = slug_match.group(1).strip()
            if "{{" not in val:
                extracted.append(("frontmatter epic_slug", val))

    # Extract branch slugs from git checkout -b / git switch -c recommendations
    for m in re.finditer(
        r"git\s+(?:switch\s+-c|checkout\s+-b)\s+(?:feature|feat|bugfix|fix|refactor|chore)/([^\s`\"';&|]+)",
        content,
    ):
        raw_branch_slug = m.group(1).strip()
        if "{{" not in raw_branch_slug:
            extracted.append(("branch recommendation slug", raw_branch_slug))

    # Also detect unsafe characters right after feature/ in git switch/checkout lines
    for m in re.finditer(
        r"git\s+(?:switch\s+-c|checkout\s+-b)\s+(?:feature|feat|bugfix|fix|refactor|chore)/([^\r\n`]+)",
        content,
    ):
        raw_full = m.group(1).strip()
        if "{{" not in raw_full and any(ch in raw_full for ch in (";", "&", "|", "$", "`", " ", "..")):
            extracted.append(("branch recommendation slug", raw_full))

    return extracted


def _split_list_tokens(raw_cell: str) -> List[str]:
    """Splits a comma/semicolon-separated markdown cell into clean tokens."""
    cleaned = raw_cell.replace("`", "").strip()
    if cleaned.lower() in NONE_VALUES:
        return []
    tokens = []
    for part in re.split(r"[,;/]+", cleaned):
        tok = part.strip()
        if tok and tok.lower() not in NONE_VALUES:
            tokens.append(tok)
    return tokens


def _extract_task_ids(raw_cell: str) -> List[str]:
    """Extracts task/feature ID tokens (e.g. T1, T2.1, F1) from a dependency cell."""
    cleaned = raw_cell.replace("`", "").strip()
    if cleaned.lower() in NONE_VALUES:
        return []
    tokens = re.findall(r"\b[A-Za-z]+[0-9]+(?:\.[0-9]+)?\b", cleaned)
    return tokens


def parse_markdown_inventory(content: str) -> Tuple[
    Dict[str, Set[str]],
    Dict[str, str],
    Dict[str, Set[str]],
    Dict[str, Set[str]],
]:
    """
    Parses Markdown Task Inventory tables and Batch bullet items.
    Returns:
      - dependencies: {task_id: set(dep_task_ids)}
      - sizes: {task_id: size_tag}
      - contracts_introduced: {task_id: set(contract_names)}
      - contracts_consumed: {task_id: set(contract_names)}
    """
    dependencies: Dict[str, Set[str]] = {}
    sizes: Dict[str, str] = {}
    contracts_introduced: Dict[str, Set[str]] = {}
    contracts_consumed: Dict[str, Set[str]] = {}

    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and line.endswith("|"):
            header_cells = [c.strip().lower() for c in line.strip("|").split("|")]
            # Check if next line is separator
            if i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
                id_idx = None
                size_idx = None
                dep_idx = None
                intro_idx = None
                cons_idx = None
                for idx, col in enumerate(header_cells):
                    if id_idx is None and col in ("id", "task id", "step / feature", "slice", "task"):
                        id_idx = idx
                    elif size_idx is None and "size" in col:
                        size_idx = idx
                    elif dep_idx is None and ("dep" in col or "depends on" in col):
                        dep_idx = idx
                    elif intro_idx is None and ("introduced" in col or "introduces" in col):
                        intro_idx = idx
                    elif cons_idx is None and ("consumed" in col or "consumes" in col):
                        cons_idx = idx

                i += 2
                while i < len(lines):
                    row_line = lines[i].strip()
                    if not (row_line.startswith("|") and row_line.endswith("|")):
                        break
                    cells = [c.strip() for c in row_line.strip("|").split("|")]
                    if id_idx is not None and id_idx < len(cells):
                        raw_id_cell = cells[id_idx]
                        id_match = re.search(r"\b([TF][0-9]+(?:\.[0-9]+)?)\b", raw_id_cell)
                        if id_match:
                            task_id = id_match.group(1)
                            dependencies.setdefault(task_id, set())
                            contracts_introduced.setdefault(task_id, set())
                            contracts_consumed.setdefault(task_id, set())

                            if size_idx is not None and size_idx < len(cells):
                                sz_cell = cells[size_idx].replace("`", "").strip().upper()
                                sz_match = re.search(r"\[(S|M|L|XL|SPIKE)\]", sz_cell)
                                if sz_match:
                                    sizes[task_id] = f"[{sz_match.group(1)}]"
                                elif sz_cell in ("S", "M", "L", "XL", "SPIKE"):
                                    sizes[task_id] = f"[{sz_cell}]"

                            if dep_idx is not None and dep_idx < len(cells):
                                for dep in _extract_task_ids(cells[dep_idx]):
                                    dependencies[task_id].add(dep)

                            if intro_idx is not None and intro_idx < len(cells):
                                for c_name in _split_list_tokens(cells[intro_idx]):
                                    if "{{" not in c_name:
                                        contracts_introduced[task_id].add(c_name)

                            if cons_idx is not None and cons_idx < len(cells):
                                for c_name in _split_list_tokens(cells[cons_idx]):
                                    if "{{" not in c_name:
                                        contracts_consumed[task_id].add(c_name)
                    i += 1
                continue
        i += 1

    # Also inspect atomic batch list items (e.g., "- [ ] **T1.1:** ... `[S]`")
    current_task: Optional[str] = None
    for line in lines:
        task_bullet = re.search(
            r"^\s*-\s*\[[ xX]\]\s*\*\*([TF][0-9]+(?:\.[0-9]+)?)\s*:?\*\*(.*)$", line
        )
        if task_bullet:
            current_task = task_bullet.group(1)
            rest = task_bullet.group(2)
            dependencies.setdefault(current_task, set())
            contracts_introduced.setdefault(current_task, set())
            contracts_consumed.setdefault(current_task, set())
            sz_match = re.search(r"\[(S|M|L|XL|SPIKE)\]", rest, re.IGNORECASE)
            if sz_match:
                sizes[current_task] = f"[{sz_match.group(1).upper()}]"
            continue

        if current_task:
            intro_match = re.search(
                r"\*Contracts?\s+Introduced:\*\s*(.+)$", line, re.IGNORECASE
            )
            if intro_match:
                for tok in _split_list_tokens(intro_match.group(1)):
                    if "{{" not in tok:
                        contracts_introduced[current_task].add(tok)

            cons_match = re.search(
                r"\*(?:Contracts?\s+)?Consumes?:\*\s*(.+)$", line, re.IGNORECASE
            )
            if cons_match:
                raw_cons = cons_match.group(1)
                # Strip parenthetical notes like "(Implements concrete adapter)"
                raw_cons_clean = re.sub(r"\([^)]*\)", "", raw_cons)
                for tok in _split_list_tokens(raw_cons_clean):
                    if "{{" in tok:
                        continue
                    if re.match(r"^[TF][0-9]+(?:\.[0-9]+)?$", tok):
                        dependencies[current_task].add(tok)
                    else:
                        contracts_consumed[current_task].add(tok)

    return dependencies, sizes, contracts_introduced, contracts_consumed


def parse_mermaid_dag(content: str) -> Tuple[Dict[str, Set[str]], Dict[str, str]]:
    """
    Extracts task dependencies and inline size tags from Mermaid `flowchart` or `graph` blocks.
    """
    deps: Dict[str, Set[str]] = {}
    sizes: Dict[str, str] = {}
    mermaid_blocks = re.findall(r"```mermaid\r?\n(.*?)```", content, re.DOTALL)
    for block in mermaid_blocks:
        if not re.search(r"^\s*(?:flowchart|graph)\s+(?:TD|TB|LR|RL|BT)", block, re.MULTILINE):
            continue
        for line in block.splitlines():
            clean = line.strip()
            if not clean or clean.startswith("%%") or clean.startswith("flowchart") or clean.startswith("graph"):
                continue

            # Extract inline size labels from node definitions like T1["T1: [S] Domain"]
            for node_def in re.finditer(r"\b([A-Za-z]+[0-9]+(?:\.[0-9]+)?)\s*\[[^\]]*?\[(S|M|L|XL|SPIKE)\]", clean, re.IGNORECASE):
                node_id = node_def.group(1)
                sz = f"[{node_def.group(2).upper()}]"
                sizes[node_id] = sz
                deps.setdefault(node_id, set())

            # Strip bracketed node labels before parsing edges so `-->` inside quotes doesn't confuse
            line_no_labels = re.sub(r"\[[^\]]*\]", "", clean)
            edge_match = re.search(
                r"\b([A-Za-z]+[0-9]+(?:\.[0-9]+)?)\b\s*(?:-->|==>|-\.->)\s*\b([A-Za-z]+[0-9]+(?:\.[0-9]+)?)\b",
                line_no_labels,
            )
            if edge_match:
                src, dst = edge_match.group(1), edge_match.group(2)
                deps.setdefault(src, set())
                deps.setdefault(dst, set()).add(src)

    return deps, sizes


def get_all_ancestors(node: str, deps: Dict[str, Set[str]]) -> Set[str]:
    """Returns all transitive dependency ancestors of `node` in an acyclic graph."""
    visited: Set[str] = set()
    stack = list(deps.get(node, set()))
    while stack:
        curr = stack.pop()
        if curr not in visited:
            visited.add(curr)
            for parent in deps.get(curr, set()):
                if parent not in visited:
                    stack.append(parent)
    return visited


def validate_dag_content(
    content: str,
    filepath_str: str = "<memory>",
    explicit_slug: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """
    Validates a decomposition markdown document for:
    1. Slug sanitization
    2. Task sizing ([S], [M], [SPIKE] allowed; [L], [XL] rejected)
    3. Acyclic dependency graph via graphlib.TopologicalSorter
    4. Contract topological order (introducers must be ancestors of consumers)
    """
    errors: List[str] = []

    # 1. Slug validation
    if explicit_slug is not None:
        err = validate_slug(explicit_slug, "--slug argument")
        if err:
            errors.append(err)

    for ctx, extracted_slug in extract_slugs_from_content(content):
        err = validate_slug(extracted_slug, ctx)
        if err:
            errors.append(err)

    # 2. Parse Markdown inventory & Mermaid flowchart
    md_deps, md_sizes, contracts_intro, contracts_cons = parse_markdown_inventory(content)
    mm_deps, mm_sizes = parse_mermaid_dag(content)

    # Merge dependencies and sizes
    all_deps: Dict[str, Set[str]] = {}
    for node, dset in md_deps.items():
        all_deps.setdefault(node, set()).update(dset)
        for dep in dset:
            all_deps.setdefault(dep, set())
    for node, dset in mm_deps.items():
        all_deps.setdefault(node, set()).update(dset)
        for dep in dset:
            all_deps.setdefault(dep, set())

    all_sizes: Dict[str, str] = {}
    all_sizes.update(mm_sizes)
    all_sizes.update(md_sizes)

    # Also scan raw content for any forbidden [L] or [XL] slice tags in tables or task bullets
    for line in content.splitlines():
        if re.search(r"^\s*(?:\||-\s*\[[ xX]\])", line):
            bad_size = re.search(r"\[(L|XL)\]", line, re.IGNORECASE)
            if bad_size:
                errors.append(
                    f"Forbidden slice size '[{bad_size.group(1).upper()}]' detected in line: '{line.strip()}'. "
                    "All slices must be decomposed into [S], [M], or [SPIKE]."
                )

    for task_id, sz in sorted(all_sizes.items()):
        if sz in FORBIDDEN_SIZES or sz not in ALLOWED_SIZES:
            msg = (
                f"Task '{task_id}' has invalid size '{sz}'. "
                f"Allowed sizes: {sorted(ALLOWED_SIZES)} (monolithic [L]/[XL] slices are prohibited)."
            )
            if msg not in errors:
                errors.append(msg)

    if not all_deps:
        errors.append(
            f"No task dependency graph or Task Inventory table found in '{filepath_str}'."
        )
        return False, errors

    # 3. Cycle detection using graphlib.TopologicalSorter
    sorter = graphlib.TopologicalSorter(all_deps)
    try:
        _ = list(sorter.static_order())
    except graphlib.CycleError as exc:
        cycle_nodes = exc.args[1] if len(exc.args) > 1 else exc.args
        errors.append(
            f"Cycle detected in task dependency graph (graphlib.CycleError): {cycle_nodes}"
        )
        return False, errors

    # 4. Contract topological order verification
    # Map each introduced contract to the task(s) that introduce it
    introducer_map: Dict[str, Set[str]] = {}
    for task_id, c_set in contracts_intro.items():
        for c_name in c_set:
            introducer_map.setdefault(c_name, set()).add(task_id)

    for consumer_task, consumed_set in sorted(contracts_cons.items()):
        ancestors = get_all_ancestors(consumer_task, all_deps)
        for c_name in sorted(consumed_set):
            if c_name in introducer_map:
                introducers = introducer_map[c_name]
                # If consumer_task itself introduces it, or at least one introducer is an ancestor, it's valid
                if consumer_task not in introducers and not (introducers & ancestors):
                    errors.append(
                        f"Contract topological order violation: Task '{consumer_task}' consumes contract "
                        f"'{c_name}', which is introduced by {sorted(introducers)}, but {sorted(introducers)} "
                        f"is not an ancestor dependency of '{consumer_task}' (ancestors: {sorted(ancestors)})."
                    )

    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministically validate Epic/Task Decomposition DAG, slice sizing, contract ownership order, and slug safety."
    )
    parser.add_argument(
        "filepath",
        nargs="?",
        default=None,
        help="Path to the decomposition Markdown file (e.g., 01-concepcao/epic-[slug].md).",
    )
    parser.add_argument(
        "--slug",
        dest="slug",
        default=None,
        help="Optional epic or feature slug to validate against strict regex ^[a-z0-9]+(-[a-z0-9]+)*$.",
    )
    args = parser.parse_args()

    if args.slug and not args.filepath:
        err = validate_slug(args.slug, "--slug argument")
        if err:
            print(f"❌ [DAG Validation Failed]:\n   - {err}")
            return 1
        print("[PASS]: DAG_VERIFIED")
        return 0

    if not args.filepath:
        print("❌ Error: Please provide a decomposition markdown file path or --slug.")
        return 1

    target = Path(args.filepath)
    if not target.exists():
        print(f"❌ Error: Decomposition file does not exist: {target}")
        return 1

    content = target.read_text(encoding="utf-8", errors="replace")
    is_valid, errors = validate_dag_content(content, str(target), explicit_slug=args.slug)
    if not is_valid:
        print(f"❌ [DAG Validation Failed] {target}:")
        for err in errors:
            print(f"   - {err}")
        return 1

    print("[PASS]: DAG_VERIFIED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
