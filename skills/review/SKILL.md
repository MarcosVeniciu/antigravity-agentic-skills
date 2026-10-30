---
name: review
description: Conducts rigorous, script-first multi-domain code reviews across the git diff in 5 parallel Flash subagents (Architecture + SDD Drift Gate, OWASP Security, AST Quality, Performance, Resilience).
---

# Skill: Multi-Domain Code Review (`/review`)

Executes Phase 4 audits via CLI scanners and 5 parallel subagents (`Model: "flash"`) across git diff. Walkthrough: [`review-example.md`](./examples/review-example.md).

## Modes & Scopes

| Mode | Trigger & Invariant | Actions & Commits |
| :--- | :--- | :--- |
| **A: Audit** | Default. Zero source edits; writes 5 reports to `02-auditorias/`. | Read-only; updates `01-concepcao/dod-[slug].md`. |
| **B: Fix (`--fix`)** | Surgical fixes applied centrally. | Re-runs scanners + pytest; stages explicitly (`git add <f1> <f2>`); commits checkpoints. |

- **Entry Gate:** Test suite green (`python -m pytest -v`).
- **Diff & Taint:** `git --no-pager diff develop...HEAD --name-only`. Trace Call Hierarchy 1–2 levels outside diff.

## Execution Pipeline

| Step | Actor | Technical Directive & Invariants | Command / Artifact |
| :--- | :--- | :--- | :--- |
| **1. Pre-Flight** | Orchestrator | Run test suite gate and 4 CLI scanners across diff files. | `python -m pytest -v`<br>CLI table below |
| **2. Map (5 Audits)** | 5x Subagents (`flash`) | Parallel dispatch (writes to `02-auditorias/`; zero edits to `src/`). Trace Call Hierarchy 1-2 levels. | [`review-subagents.md`](./references/review-subagents.md)<br>[`audit-report-template.md`](./resources/audit-report-template.md)<br>[Arch](./references/review-architecture.md), [Security](./references/review-security.md), [Quality](./references/review-quality.md), [Perf](./references/review-performance.md), [Resilience](./references/review-resilience.md) |
| **3. Reduce & Gates** | Orchestrator | Mode A: verify 5 reports; mark Living DoD. Mode B (`--fix`): apply surgical fixes; re-run scanners + pytest; stage explicitly (`git add <f1> <f2>`); commit checkpoints and phase commit. | `python -m pytest -v`<br>`git commit -m "audit(review): specialized domain audits completed for [slug]"` |

## Pre-Flight Scanners & CLI Gate

| Check | CLI Command | Target Invariant |
| :--- | :--- | :--- |
| **SDD Drift** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <modified_files> --check-files --pivots 02-auditorias/pivots-[slug].md` | SDD contract parity. |
| **Boundary** | `python skills/review/scripts/check_arch_boundaries.py <modified_files>` | Flags forbidden layer imports. |
| **Sinks** | `python skills/review/scripts/scan_sinks.py <modified_files>` | Flags dangerous sinks. |
| **Complexity** | `python skills/review/scripts/ast_complexity.py <modified_files>` | McCabe $V(G) \le 10$ & nested loops. |
