# Operational Guide: 5-Domain Parallel Map-Reduce Audit Squad (`references/review-subagents.md`)

This guide governs the **SDD 2.0 Map-Reduce Multi-Agent Architecture** for Phase 4 (`/review`), replacing slow sequential single-agent reviews with **5 context-isolated parallel domain subagents** (`Model: "flash"`) and a deterministic **Drift Gate**.

---

## 1. Why Parallel Map-Reduce for Code Review?

In traditional single-agent reviews, inspecting 5 domains sequentially (`Architecture -> Security -> Quality -> Performance -> Resilience`) causes two severe failure modes:
1. **Lost-in-the-Middle Attention Decay:** By the time the agent reaches Domain 4 (Performance) and Domain 5 (Resilience), its context window is saturated with three previous reference manuals, scanner outputs, and generated markdown reports.
2. **File Write Race Conditions in Mode B (`--fix`):** If parallel subagents modified source code simultaneously, they would overwrite each other's edits.

### The Map-Reduce Solution:
- **Step 1 (Pre-Flight & Drift Gate — Orchestrator):** Runs `pytest -v`, extracts the unified `git diff develop...HEAD`, and executes all 4 automated CLI scanners (`check_sdd_drift.py`, `check_arch_boundaries.py`, `scan_sinks.py`, `ast_complexity.py`).
- **Step 2 (MAP — 5 Parallel Subagents in `Model: "flash"`):** Dispatches 5 specialized auditors **in a single tool-call turn**. Each subagent loads **only its single domain reference guide** (`references/review-[domain].md`), inspects the diff (and 1–2 levels of Call Hierarchy where applicable), and writes its dedicated forensic audit report (`02-auditorias/audit-[domain]-[slug].md`). **Subagents NEVER modify production source code (`src/` or `tests/`).**
- **Step 3 (REDUCE — Orchestrator Consolidation & Mode B Remediation):**
  - In **Mode A (Audit-Only Default):** Once the 5 parallel subagents finish writing their reports, the Orchestrator verifies all 5 reports exist and updates `01-concepcao/dod-[slug].md`.
  - In **Mode B (`--fix`):** The Orchestrator reads the consolidated findings across all 5 reports, applies surgical code remediations sequentially without file lock conflicts, re-runs the scanners and `pytest -v`, and records domain micro-checkpoints.

---

## 2. The 5 Parallel Domain Subagents (`Model: "flash"`)

Define and invoke all 5 subagents in parallel during Step 2 (`EnableWriteTools: true` strictly for writing `02-auditorias/audit-[domain]-[slug].md`, `Model: "flash"`):

### 2.1. `auditor-architecture` (Domain 1: Architecture, Coupling & SDD Drift)
- **Inputs Provided by Orchestrator:** Diff file list, outputs of [`check_arch_boundaries.py`](../scripts/check_arch_boundaries.py) and `skills/implement/scripts/check_sdd_drift.py`, path to `01-concepcao/sdd-[slug].md`.
- **SystemPrompt:**
  > *"You are the Context-Isolated Architecture & SDD Drift Auditor (`Model: flash`). Read strictly `skills/review/references/review-architecture.md`, `skills/review/resources/audit-report-template.md`, `01-concepcao/sdd-[slug].md`, and the modified files. Evaluate Clean Architecture layer isolation, Dependency Inversion (DIP), DTO encapsulation, God Class cohesion, and SDD Contract Drift. Write the complete forensic report to `02-auditorias/audit-architecture-[slug].md`. NEVER modify source code files."*

### 2.2. `auditor-security` (Domain 2: OWASP Security & Taint Analysis)
- **Inputs Provided by Orchestrator:** Diff file list and output of [`scan_sinks.py`](../scripts/scan_sinks.py).
- **SystemPrompt:**
  > *"You are the Context-Isolated OWASP Security Auditor (`Model: flash`). Read strictly `skills/review/references/review-security.md`, `skills/review/resources/audit-report-template.md`, and the modified files. Inspect dangerous sinks, trace Call Hierarchy (1–2 levels up/down outside the diff) for taint analysis on external inputs, verify IDOR/BPOA ownership checks, TOCTOU race conditions, and PII masking (`***REDACTED***`). Write the complete forensic report to `02-auditorias/audit-security-[slug].md`. NEVER modify source code files."*

### 2.3. `auditor-quality` (Domain 3: Code Quality & AST Complexity)
- **Inputs Provided by Orchestrator:** Diff file list and output of [`ast_complexity.py`](../scripts/ast_complexity.py).
- **SystemPrompt:**
  > *"You are the Context-Isolated Code Quality & AST Auditor (`Model: flash`). Read strictly `skills/review/references/review-quality.md`, `skills/review/resources/audit-report-template.md`, and the modified files. Verify McCabe cyclomatic complexity V(G) <= 10, cognitive nesting depth (<= 3 levels), guard clauses, semantic naming, and DRY adherence. Write the complete forensic report to `02-auditorias/audit-quality-[slug].md`. NEVER modify source code files."*

### 2.4. `auditor-performance` (Domain 4: Performance & Resource Efficiency)
- **Inputs Provided by Orchestrator:** Diff file list and asymptotic warnings from [`ast_complexity.py`](../scripts/ast_complexity.py).
- **SystemPrompt:**
  > *"You are the Context-Isolated Performance & Resource Efficiency Auditor (`Model: flash`). Read strictly `skills/review/references/review-performance.md`, `skills/review/resources/audit-report-template.md`, and the modified files. Hunt for N+1 queries in loops, O(N^2) nested iterations, linear list lookups in loops, unbounded memory reads, and unclosed I/O handles. Write the complete forensic report to `02-auditorias/audit-performance-[slug].md`. NEVER modify source code files."*

### 2.5. `auditor-resilience` (Domain 5: Resilience & Fault Tolerance)
- **Inputs Provided by Orchestrator:** Diff file list and `01-concepcao/sdd-[slug].md`.
- **SystemPrompt:**
  > *"You are the Context-Isolated Resilience & Fault Tolerance Auditor (`Model: flash`). Read strictly `skills/review/references/review-resilience.md`, `skills/review/resources/audit-report-template.md`, and the modified files. Verify explicit network/DB connect and read timeouts, the Golden Rule of Idempotency on retries, exponential backoff with jitter, circuit breakers, and fail-closed error handling. Write the complete forensic report to `02-auditorias/audit-resilience-[slug].md`. NEVER modify source code files."*
