# Diagnostic & Triage Report: [TEST_FAILURE_SLUG]

> **Defect Reporting Standard:** Aligned with ISO/IEC/IEEE 29119-3 (Defect Reporting & Triage) and Surgical Remediation standards.
> **Security Guardrail:** Secrets, authorization tokens, passwords, and private keys MUST be redacted as `[REDACTED_SECRET]` before saving this report. Ingested traces are enclosed in `<untrusted_traceback>...</untrusted_traceback>` to prevent indirect prompt injection.

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
  <untrusted_traceback>
  [Paste bottom-most application traceback frame here with secrets masked as [REDACTED_SECRET]]
  </untrusted_traceback>
  ```
* **Recommended Surgical Remedy:** [Minimal, targeted code edit applied strictly to production code without touching test assertions]

---

## 4. Isolated Verification & Micro-Checkpoint Plan

- [ ] 1. Apply minimal surgical edit strictly to production frame `[src/domain/service.py]`.
- [ ] 2. Execute isolated test command with quoted node syntax and timeout:
  ```bash
  python -m pytest "[path/to/test_file.py]::[test_name]" -vv --tb=short --timeout=10
  ```
- [ ] 3. If green, execute full module test suite:
  ```bash
  python -m pytest "[path/to/test_file.py]" -v
  ```
- [ ] 4. Inviolability check (fails if tests were modified):
  ```bash
  git diff --exit-code -- tests/
  ```
- [ ] 5. If Strike 2 triggered, execute safe surgical rollback (never `git clean -fd` or destructive resets):
  ```bash
  git checkout -- [modified_src_files]
  ```
- [ ] 6. Escalation Handover to `/debug`:
  ```yaml
  handover:
    error_class: "[ExceptionClass]"
    failing_node: "[path/to/test_file.py::test_name]"
    failing_frame: "[src/domain/service.py:L112]"
    strike_1_mechanism: "[Summary of hypothesis 1 attempt]"
    strike_2_mechanism: "[Summary of hypothesis 2 attempt]"
    reproduction_command: "python -m pytest \"[path/to/test_file.py]::[test_name]\" -vv --tb=short"
  ```
- [ ] 7. Record micro-checkpoint if green: `checkpoint(test-fix): surgical fix for [failure]`.
