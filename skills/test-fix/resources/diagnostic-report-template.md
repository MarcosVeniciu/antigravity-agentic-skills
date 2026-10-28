# Diagnostic & Triage Report: [TEST_FAILURE_SLUG]

> **Defect Reporting Standard:** Aligned with ISO/IEC/IEEE 29119-3 (Defect Reporting & Triage) and Surgical Remediation standards.

**Diagnosis Date:** [YYYY-MM-DD]  
**Component:** `[path/to/production/component.py]`  
**Target Test Node:** `[path/to/test_file.py::test_name]`  
**Double-Strike Status:** Strike 0 (Initial) | Strike 1 (Refining) | Green (Passed) | Strike 2 (Escalated to /debug)  

---

## 1. Executive Summary
* **Failing Node:** `[path/to/test_file.py::test_name]`
* **Primary Exception:** `[e.g., TypeError: unsupported operand type(s) for *: 'NoneType' and 'float']`
* **Defect Classification:** [Type Mismatch | Logic/Calculation | Boundary/Contract | State/Lifecycle | Mock/Boundary Leak]
* **Triage Summary:** [Concise 1-2 sentence overview of the defect trigger and production frame where invalid state surfaced.]

---

## 2. Test Failure Traceability & Triage Matrix

| ID | Test Node | Bottom Traceback Frame | Exception Class | Defect Category | Diagnostic Status & Traceability |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `[TFX-01]` | `[tests/unit/test_service.py::test_calc]` | `[src/domain/service.py:112]` | `TypeError` | Type Mismatch | 🔴 **Failing** ([see Diagnosis 1](#-diagnosis-1-root-cause-isolation)) |

---

## 3. Surgical Diagnosis & 1-Sentence Root Cause

#### 📌 Diagnosis 1: [Root Cause Isolation]
* **Location:** `[src/domain/service.py:L112]` (format in report as clickable IDE link `file:///absolute/path/to/service.py#L112`)
* **1-Sentence Root Cause:** `[Category]: [Target Component] fails because [exact defect mechanism], causing [observed failure].`
* **Primary Frame Evidence:**
  ```text
  [Paste bottom-most application traceback frame here]
  ```
* **Recommended Surgical Remedy:** [Minimal, targeted code edit applied strictly to production code without touching test assertions]

---

## 4. Isolated Verification & Micro-Checkpoint Plan

- [ ] 1. Apply minimal surgical edit strictly to production frame `[src/domain/service.py]`.
- [ ] 2. Execute isolated test command:
  ```bash
  python -m pytest [path/to/test_file.py] -k [test_name] -v
  ```
- [ ] 3. If green, execute full module test suite:
  ```bash
  python -m pytest [path/to/test_file.py] -v
  ```
- [ ] 4. If Strike 2 triggered, execute rollback (`git reset --hard HEAD; git clean -fd`) and export handover payload to `/debug`.
- [ ] 5. Record micro-checkpoint: `checkpoint(test-fix): surgical fix for [failure]`.
