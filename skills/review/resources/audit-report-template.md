# Audit Report: [DOMAIN] — [FEATURE_SLUG]

> **Specification Standard:** Aligned with ISO 19011 (Management Systems Audit), IEEE 829 / ISO 29119 (Traceability Matrix), and Forensic Chain of Custody standards.

**Audit Date:** [YYYY-MM-DD]  
**Audited Domain:** [Architecture & Coupling | OWASP Security | Code Quality & AST | Performance | Resilience]  
**Git Scope:** `[base-branch]...[head-branch]` (Commit: `[git-sha]`)  
**Overall Status:** 🟢 Compliant | 🟡 Attention Required | 🔴 Non-Compliant  

---

## 1. Executive Summary
* **Scope Overview:** Audited `[N]` modified files across the feature changeset.
* **Automated Scanners Executed:** `[Scanner CLI commands executed and execution status]`
* **Unit & Integration Test Gate:** `[100% Green (N/N tests passing)]`
* **General Diagnostic:** [Concise 2-3 sentence technical diagnosis of the domain health, identifying key risk areas or confirming robust isolation.]

---

## 2. Forensic Traceability & Compliance Matrix

| ID | File & Line | Audit Rule / Principle | Primary Evidence / Tool | Severity | Status & Traceability |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `[DOM-01]` | `[path/to/file.py:45]` | [e.g., Layer Boundary Isolation / Dangerous Sink] | [Linter / Scanner / AST Inspection] | [Low/Med/High] | 🟢 **100% Compliant** |
| `[DOM-02]` | `[path/to/service.py:112]` | [e.g., Cyclomatic Complexity V(G) <= 10] | [ast_complexity.py / AST Parser] | [Medium] | 🟡 **Attention** ([see Finding 1](#-finding-1-title)) |
| `[DOM-03]` | `[path/to/repo.py:78]` | [e.g., Mandatory Timeout on Network Call] | [Inspection of httpx.Client] | [High] | 🔴 **Non-Compliant** ([see Finding 2](#-finding-2-title)) |

---

## 3. Forensic Findings & Points of Attention

#### 📌 Finding 1: [Title of Attention Point or Violation]
* **Location:** `[path/to/file.py:L112-L125]` (format in report as clickable IDE link `file:///absolute/path/to/file.py#L112-L125`)
* **Observed Condition:** [Exact description of what exists in code, including code snippet or AST metric]
* **Real Evidence / Rule Violated:** [Primary evidence from scanner output, architectural rule, or security guideline]
* **Recommended Surgical Action (Mode B):** [Precise, minimal refactoring steps to achieve 100% compliance without side effects]

#### 📌 Finding 2: [Title of Critical Finding]
* **Location:** `[path/to/repo.py:L78]` (format in report as clickable IDE link `file:///absolute/path/to/repo.py#L78`)
* **Observed Condition:** [Description of non-compliant implementation]
* **Real Evidence / Rule Violated:** [Specific standard or vulnerability CVE/CWE reference]
* **Recommended Surgical Action (Mode B):** [Minimal, surgical remediation code example]

---

## 4. Remediation Plan & Handover Checkpoints

- [ ] 1. Apply surgical fix for Finding 1 in `path/to/file.py`.
- [ ] 2. Apply surgical fix for Finding 2 in `path/to/repo.py`.
- [ ] 3. Re-execute automated domain scanner to confirm violation clearance.
- [ ] 4. Re-run complete test suite (`python -m pytest -v`) to guarantee zero regressions.
- [ ] 5. Record micro-checkpoint: `checkpoint(review): fixes for [domain]`.
- [ ] 6. Update Living Definition of Done in `01-concepcao/dod-[slug].md`.
