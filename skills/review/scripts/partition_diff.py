#!/usr/bin/env python3
"""
skills/review/scripts/partition_diff.py
Deterministic Git Diff Chunking & Pagination Tool for Review Subagents (Zero External Dependencies).

Enforces:
1. Prevents lost-in-the-middle context window degradation in flash subagents ([EV-REV-04]).
2. Analyzes git diff numstat (files, additions, deletions).
3. Partitions massive diffs (> 50 files or > 3,000 lines) into balanced chunks preserving
   module and directory cohesion.
4. Emits structured JSON partitions or CLI-formatted summaries for map-phase dispatch.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def get_diff_stats(
    diff_spec: str = "develop...HEAD",
    files: Optional[List[str]] = None,
) -> Tuple[bool, List[Dict[str, Any]], str]:
    """
    Retrieves file list and line change metrics using 'git diff --numstat'.
    """
    cmd = ["git", "--no-pager", "diff", "--numstat", diff_spec]
    if files:
        cmd.extend(["--"] + files)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            return False, [], f"git diff failed ({proc.stderr.strip()})"
        lines = proc.stdout.strip().splitlines()
    except Exception as e:
        return False, [], f"Could not run git diff: {e}"

    entries: List[Dict[str, Any]] = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) >= 3:
            add_str, del_str, filepath = parts[0], parts[1], parts[2]
            added = int(add_str) if add_str.isdigit() else 0
            deleted = int(del_str) if del_str.isdigit() else 0
            entries.append({
                "path": filepath.replace("\\", "/"),
                "added": added,
                "deleted": deleted,
                "lines": added + deleted,
            })

    return True, entries, "OK"


def partition_file_entries(
    entries: List[Dict[str, Any]],
    max_files: int = 50,
    max_lines: int = 3000,
) -> List[Dict[str, Any]]:
    """
    Greedily partitions entries into chunks respecting max_files and max_lines,
    keeping directory neighbours close together.
    """
    if not entries:
        return []

    # Sort entries by parent directory to maintain architectural cohesion
    sorted_entries = sorted(entries, key=lambda x: (str(Path(x["path"]).parent), x["path"]))

    partitions: List[Dict[str, Any]] = []
    current_files: List[str] = []
    current_lines = 0

    for entry in sorted_entries:
        path = entry["path"]
        lines = entry["lines"]

        # If adding this entry exceeds limits and we already have items in chunk, close chunk
        if current_files and (len(current_files) >= max_files or (current_lines + lines > max_lines and current_lines > 0)):
            partitions.append({
                "index": len(partitions) + 1,
                "file_count": len(current_files),
                "total_lines": current_lines,
                "files": list(current_files),
            })
            current_files = []
            current_lines = 0

        current_files.append(path)
        current_lines += lines

    if current_files:
        partitions.append({
            "index": len(partitions) + 1,
            "file_count": len(current_files),
            "total_lines": current_lines,
            "files": list(current_files),
        })

    return partitions


def main() -> int:
    parser = argparse.ArgumentParser(description="Git Diff Partitioning & Chunking Tool for Review Audits")
    parser.add_argument("diff_spec", nargs="?", default="develop...HEAD", help="Git diff revision range (default: 'develop...HEAD')")
    parser.add_argument("--files", nargs="*", default=None, help="Explicit file list to evaluate")
    parser.add_argument("--max-files", type=int, default=50, help="Maximum files per partition chunk (default: 50)")
    parser.add_argument("--max-lines", type=int, default=3000, help="Maximum changed lines per partition chunk (default: 3000)")
    parser.add_argument("--json", action="store_true", help="Output JSON structure of partitions")
    args = parser.parse_args()

    ok, entries, msg = get_diff_stats(diff_spec=args.diff_spec, files=args.files)
    if not ok:
        # Fallback if outside git repository or no diff
        if args.files:
            entries = [{"path": f, "added": 10, "deleted": 0, "lines": 10} for f in args.files]
        else:
            print(f"⚠️ Notice: {msg}")
            entries = []

    partitions = partition_file_entries(entries, max_files=args.max_files, max_lines=args.max_lines)

    if args.json:
        print(json.dumps({
            "total_files": len(entries),
            "total_lines": sum(e["lines"] for e in entries),
            "chunk_count": len(partitions),
            "partitions": partitions,
        }, indent=2))
        return 0

    print("======================================================================")
    print(f"       Git Diff Partitioning Analysis ({args.diff_spec})")
    print("======================================================================")
    total_files = len(entries)
    total_lines = sum(e["lines"] for e in entries)
    print(f"Total Files in Diff: {total_files}")
    print(f"Total Lines Changed: {total_lines}")
    print(f"Partitions Needed:  {len(partitions)} (Thresholds: max {args.max_files} files, max {args.max_lines} lines/chunk)")

    if len(partitions) <= 1:
        print("\n✅ Diff is within standard single-pass bounds. No multi-chunk pagination required.")
    else:
        print(f"\n⚠️  [MASSIVE DIFF DETECTED] Diff partitioned into {len(partitions)} chunks to prevent LLM context loss:")
        for p in partitions:
            print(f"   Chunk #{p['index']}: {p['file_count']} files, {p['total_lines']} lines")

    return 0


if __name__ == "__main__":
    sys.exit(main())

