# 5-Domain Review Subagents (`references/review-subagents.md`)

Map-Reduce spec for `/review`. Template: [`../resources/audit-report-template.md`](../resources/audit-report-template.md).

## 1. Map-Reduce Pipeline

| Step | Actor | Invariants & Directives | Tools & Outputs |
| :--- | :--- | :--- | :--- |
| **1. Pre-Flight** | Orchestrator | Run test suite, git diff, and 4 CLI scanners. | `pytest -v`, `git diff`, [`check_arch_boundaries.py`](../scripts/check_arch_boundaries.py), [`scan_sinks.py`](../scripts/scan_sinks.py), [`ast_complexity.py`](../scripts/ast_complexity.py), `check_sdd_drift.py`. |
| **2. MAP** | 5x Subagents (`flash`) | Parallel dispatch. Read domain guide, inspect diff + Call Hierarchy (1-2 levels). Zero source edits. | `EnableWriteTools: true` for `02-auditorias/`. Read-only on `src/`. |
| **3. REDUCE** | Orchestrator | Mode A: verify reports; mark DoD. Mode B (`--fix`): apply fixes in `src/`, re-run scanners + pytest, stage files explicitly, commit checkpoints. | Stage explicitly (never `git add .`); commit `checkpoint(review): fixes for [domain]`. |

## 2. Subagent Registry & SystemPrompts

All auditors: `Model: "flash"`, `EnableWriteTools: true` (strictly `02-auditorias/`).

| Agent | Focus & Inputs | Target Report |
| :--- | :--- | :--- |
| **`auditor-architecture`** | [`review-architecture.md`](./review-architecture.md), `check_arch_boundaries.py`, `check_sdd_drift.py`, `01-concepcao/sdd-[slug].md` | `audit-architecture-[slug].md` |
| **`auditor-security`** | [`review-security.md`](./review-security.md), `scan_sinks.py`, Call Hierarchy (1-2 levels) | `audit-security-[slug].md` |
| **`auditor-quality`** | [`review-quality.md`](./review-quality.md), `ast_complexity.py` ($V(G) \le 10$) | `audit-quality-[slug].md` |
| **`auditor-performance`** | [`review-performance.md`](./review-performance.md), `ast_complexity.py` | `audit-performance-[slug].md` |
| **`auditor-resilience`** | [`review-resilience.md`](./review-resilience.md), `01-concepcao/sdd-[slug].md` timeouts | `audit-resilience-[slug].md` |

### SystemPrompt Template
> "Role: [Domain] Auditor (flash). Read review-[domain].md, audit-report-template.md, specs, diff. Execute: (1) Arch: boundaries, DIP, DTO, SDD drift; (2) Security: OWASP, sinks, taint (1-2 levels outside diff), IDOR, TOCTOU, PII (***REDACTED***); (3) Quality: McCabe V(G) <= 10, depth <= 3; (4) Perf: N+1, O(N^2), leaks; (5) Resilience: timeouts, retries, jitter. Write report to 02-auditorias/audit-[domain]-[slug].md. NEVER edit source files."
