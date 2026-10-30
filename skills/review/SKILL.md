---
name: review
description: Conducts rigorous, script-first multi-domain code reviews across the git diff in 5 parallel Flash subagents (Architecture + SDD Drift Gate, OWASP Security, AST Quality, Performance, Resilience).
---

# Skill: Multi-Domain Code Review (`/review`)

Executes Phase 4 audits via CLI scanners and 5 parallel subagents (`Model: "flash"`) across git diff. Walkthrough: [`review-example.md`](./examples/review-example.md).

## Modes & Scopes

| Mode | Trigger & Invariant | Actions & Commits |
| :--- | :--- | :--- |
| **A: Audit** | Default. Zero source edits; Orchestrator writes 5 reports to `02-auditorias/`. | Read-only subagents (`EnableWriteTools: false`); updates `01-concepcao/dod-[slug].md`. |
| **B: Fix (`--fix`)** | Surgical fixes applied centrally by Orchestrator. | Re-runs scanners + pytest; stages explicitly (`git add <f1> <f2>`); commits checkpoints. |

- **Static-First Entry Gate (`[REV-ASI05-01]`):** Run all 4 static AST/sink CLI scanners (`scan_sinks.py`, `check_arch_boundaries.py`, `ast_complexity.py`, `check_sdd_drift.py`) **FIRST** before executing `python -m pytest -v`. Security Rationale: static AST/sink analysis must pass (zero critical RCE/command injection sinks in diff) before dynamically importing and executing untrusted code or `conftest.py` fixtures via `pytest`.
- **Diff & Taint:** `git --no-pager diff develop...HEAD --name-only`. Run `python skills/review/scripts/partition_diff.py develop...HEAD` if diff exceeds 50 files or 3,000 lines ([EV-REV-04]). Wrap audited diffs in `<untrusted_diff>...</untrusted_diff>` and trace Call Hierarchy 1–2 levels outside diff.

## Execution Pipeline

| Step | Actor | Technical Directive & Invariants | Command / Artifact |
| :--- | :--- | :--- | :--- |
| **1. Pre-Flight** | Orchestrator | **1st:** Run the 4 deterministic static CLI scanners across diff files (must pass zero critical RCE sinks). **2nd:** Execute `python -m pytest -v`. | 1. CLI scanners table below<br>2. `python -m pytest -v` |
| **2. Map (5 Audits)** | 5x Subagents (`flash`) | Chunk diff via `partition_diff.py` if massive; parallel dispatch with `EnableWriteTools: false` (read-only). Wrap code in `<untrusted_diff>...</untrusted_diff>`. Subagents return structured Markdown reports to Orchestrator. Trace Call Hierarchy 1–2 levels. | [`review-subagents.md`](./references/review-subagents.md)<br>[`audit-report-template.md`](./resources/audit-report-template.md)<br>[Arch](./references/review-architecture.md), [Security](./references/review-security.md), [Quality](./references/review-quality.md), [Perf](./references/review-performance.md), [Resilience](./references/review-resilience.md) |
| **3. Reduce & Gates** | Orchestrator | Persist the 5 returned reports to `02-auditorias/audit-[domain]-[slug].md`. Mode A: mark Living DoD. Mode B (`--fix`): apply surgical fixes; re-run static scanners first, then `pytest -v`; stage explicitly (`git add <f1> <f2>`); commit checkpoints and phase commit. | `python -m pytest -v`<br>`git commit -m "audit(review): specialized domain audits completed for [slug]"` |

## Pre-Flight Scanners & CLI Gate (Execute Before `pytest`)

| Check | CLI Command | Target Invariant |
| :--- | :--- | :--- |
| **Sinks** | `python skills/review/scripts/scan_sinks.py <modified_files>` | Flags dangerous sinks & obfuscated AST calls (`getattr`, `__import__`, `eval`). |
| **Boundary** | `python skills/review/scripts/check_arch_boundaries.py <modified_files> [--domain-dirs core,model]` | Flags forbidden layer imports. |
| **Complexity** | `python skills/review/scripts/ast_complexity.py <modified_files>` | Enforces McCabe $V(G) \le 10$ & flags nested loops (strict exit code). |
| **SDD Drift** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <modified_files> --check-files --pivots 02-auditorias/pivots-[slug].md` | SDD contract parity. |
