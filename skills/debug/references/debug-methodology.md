# Forensic Investigation Methodology & The 5 Whys Framework

Methodology specifications, 5 Whys derivation, and RCA schema for [`../SKILL.md`](../SKILL.md) and [`../resources/rca-template.md`](../resources/rca-template.md).

## 1. Scientific Method Protocol

| Phase | Objective | Operational Invariants |
| :--- | :--- | :--- |
| **1. Observe** | Ground truth | Capture exception, stack trace, input payload, pool state. Zero guesswork. |
| **2. Hypothesize** | Competing causes | Formulate $H_1$ (primary failure mechanism) and $H_2$ (concurrency/alternative cause). |
| **3. Experiment** | Automated probing | Author isolated characterization tests or MRE (`scripts/reproduce_*.py`). |
| **4. Analyze** | Falsification | Reject invalidated hypotheses; confirm surviving hypothesis with positive assertions. |
| **5. Conclude** | RCA & permanent fix | Submit RCA gate, verify deterministic Red -> Green, ensure zero regressions. |

---

## 2. The 5 Whys Framework (Test Escape Root Cause)

| Level | Diagnostic Focus | Example |
| :--- | :--- | :--- |
| **Why 1** | Visible symptom | Connection pool exhausted. |
| **Why 2** | Enabling condition | Connections from failed worker tasks never returned. |
| **Why 3** | Logic / state defect | Unhandled exception aborted execution before `.release()`. |
| **Why 4** | Architectural omission | Connection acquisition lacked async context manager / `try...finally` guard. |
| **Why 5 (Mandatory)** | **Automated Test Escape** | Unit tests used dummy mocks without connection lifecycle tracking under exceptions. |

---

## 3. Governance & Regression Safeguards

| Component | Directive & Enforcement |
| :--- | :--- |
| **RCA Gate** | Instantiate `root_cause_analysis.md` via [`rca-template.md`](../resources/rca-template.md). Submit with `RequestFeedback: true`. Pause for approval. |
| **Regression Safeguard** | Author regression test; verify deterministic Red; apply fix; verify 100% Green. Recovery: `git reset --hard HEAD` on failure. |
| **Vault Archiving** | Append findings to `02-auditorias/pivots-[slug].md` via `@obsidian` and update `01-concepcao/dod-[slug].md`. |
