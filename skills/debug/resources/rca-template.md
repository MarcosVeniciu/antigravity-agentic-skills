# Root Cause Analysis (RCA) — [INCIDENT_TITLE_OR_SLUG]

> **Forensic Standard:** Aligned with NIST SP 800-86 (Forensic Techniques in Incident Response) and ISO/IEC 27037 (Digital Evidence Handling & Chain of Custody).

**Incident Date:** [YYYY-MM-DD]  
**Severity:** [P1 - Critical / P2 - High / P3 - Medium]  
**Component:** `[path/to/affected/component.py]`  
**Environment:** [Production / Staging / CI / Local Container]  
**Status:** [Investigating / Awaiting Approval / Remediated]  

---

## 1. Context & Observed Symptoms

### 1.1. Executive Summary
[Concise 2-3 sentence overview of the incident, impact on end-users or system availability, and the initial detection trigger.]

### 1.2. Error Signatures & Environment Data
* **Exception Class:** `[e.g., TimeoutError, ConnectionResetError, DeadlockDetected]`
* **HTTP Status / Exit Code:** `[e.g., 500 Internal Server Error / Exit Code 137]`
* **Runtime / Concurrency Model:** `[e.g., Python 3.12, Asyncio, Celery worker concurrency=4]`
* **Primary Traceback / Log Snippet:**
  ```text
  [Paste exact terminal error message or stack trace here]
  ```

---

## 2. Forensic 5 Whys Analysis

* **Why 1 (Observed Failure):** Why did the visible crash or symptom occur?  
  ↳ *[Answer 1]*
* **Why 2 (Direct Trigger):** Why did the immediate condition in Why 1 take place?  
  ↳ *[Answer 2]*
* **Why 3 (State / Logic Defect):** Why was the system in this invalid or vulnerable state?  
  ↳ *[Answer 3]*
* **Why 4 (Architectural / Boundary Omission):** Why was there no guard, timeout, or boundary isolation preventing this state?  
  ↳ *[Answer 4]*
* **Why 5 (Mandatory Test Suite Escape):** Why did existing automated unit/integration tests fail to catch this defect before deployment?  
  ↳ *[Answer 5: Exact reason the test suite allowed this defect to escape into runtime]*

---

## 3. Forensic Traceability & Hypothesis Matrix

| ID | Component & Frame | Investigated Hypothesis / Defect Mechanism | Primary Evidence / Falsification Probe | Diagnostic Status & Traceability |
| :--- | :--- | :--- | :--- | :---: |
| **H1** | `[path/to/caller.py:42]` | [Hypothesis 1: External gateway timeout or network degradation] | [Probe with network latency simulation in MRE] | 🟢 **Falsified** |
| **H2** | `[path/to/component.py:88]` | [Hypothesis 2: Unhandled exception leads to connection pool leak] | [Monitor pool.checkedout() count during simulated failure] | 🔴 **Confirmed Root Cause** ([see Finding 1](#-finding-1-root-cause-isolation)) |

---

## 4. Forensic Findings & Root Cause Isolation

#### 📌 Finding 1: [Root Cause Isolation Title]
* **Location:** `[path/to/component.py:L88]` (format in report as clickable IDE link `file:///absolute/path/to/component.py#L88`)
* **Observed Condition:** [Exact defect mechanism, unhandled edge condition, or leaky state in production code]
* **Real Evidence & Ground Truth:** [Deterministic reproduction trace, log hash, or pool metric evidence]
* **Derivation from 5 Whys:** [Summary of Why 1 through Why 5 chain]
* **Recommended Surgical Action:** [Minimal, targeted code fix to eradicate defect mechanism]

---

## 5. Solution Alternatives & Trade-Offs

### Option A: Recommended Surgical Fix
* **Description:** [Detailed description of surgical changes in production code]
* **Impacted Files:** `[path/to/file.py]`
* **Pros:** [Benefits, e.g., zero breaking changes, minimal diff, high performance]
* **Cons & Risks:** [Trade-offs or edge-case risks]
* **Risk Rating:** [Low / Medium / High]

### Option B: Alternative / Architectural Fix
* **Description:** [Alternative approach, e.g., broader refactor or dependency upgrade]
* **Impacted Files:** `[path/to/files...]`
* **Pros:** [Long-term architectural advantages]
* **Cons & Risks:** [Scope expansion, higher regression risk]
* **Risk Rating:** [Low / Medium / High]

---

## 6. Verification & Regression Prevention Plan

### 6.1. Minimal Reproducible Example (MRE) / Test Plan
```bash
# Command to execute isolated reproduction test
python -m pytest [path/to/test_regression.py] -v
```

### 6.2. Permanent Regression Test Specification
* **New Test Location:** `tests/regression/test_[slug]_regression.py`
* **Verification Criteria:**
  - [ ] Test fails deterministically against unpatched code.
  - [ ] Test passes 100% green against patched code.
  - [ ] Edge cases (e.g., timeouts, cancellations, concurrency limits) covered.

---

## 7. Living Knowledge & Vault Archiving

- [ ] Persist incident summary and lessons learned to Obsidian Vault: `02-auditorias/pivots-[slug].md`.
- [ ] If architectural guidelines require updating, log ADR proposal in `00-core-rules/adrs/`.
- [ ] Update Living DoD: `01-concepcao/dod-[slug].md`.
