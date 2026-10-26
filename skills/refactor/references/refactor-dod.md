# Operational Reference: Living DoD & Evidence Matrix Standard

This guide specifies how to update the Living Definition of Done (`01-concepcao/dod-[slug].md`) and format the Refactoring Evidence Matrix for Phase 3 (`/refactor`).

---

## 1. Living Definition of Done (DoD) Integration

In the Antigravity lifecycle, the Living DoD serves as the single source of truth (SSOT) for feature completeness.
Phase 3 is governed by Section 3 of `01-concepcao/dod-[slug].md`.

### Phase 3 Checklist Criteria:
Before concluding Phase 3, the agent must verify and check all items under Phase 3:

```markdown
## 3. Refactoring & Audits (Phases 3 and 4 - /refactor and /review)
- [x] **Phase 3: Final Refactoring (`/refactor`)**
  - [x] Mandatory entry gate satisfied: 100% unit tests green before refactoring.
  - [x] Scope strictly confined to `git diff develop...HEAD`.
  - [x] Clean Code applied: guard clauses, method extraction, and named constants.
  - [x] SOLID principles applied across feature modules (SRP, OCP, LSP, ISP, DIP).
  - [x] AST cyclomatic complexity verified: $V(G) \le 10$ across all modified functions.
  - [x] Asymptotic performance heuristics verified: no $O(N^2)$ loops or linear searches in loops.
  - [x] Zero regressions: 100% unit tests passing green with no test assertion edits.
  - [x] Refactoring Evidence Matrix documented.
  - [x] Mode 3 Phase Squash executed with semantic commit message.
```

---

## 2. Refactoring Evidence Matrix Standard

Upon completing the refactoring iterations, compile and present the **Refactoring Evidence Matrix** using [`../resources/refactor-report-template.md`](../resources/refactor-report-template.md). This report must be documented in the chat handover and preserved in the execution log.

### Matrix Structure:

| Target Element | Code Smell / Principle | Technique Applied | $V(G)$ Before | $V(G)$ After | Test Suite Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `<file_path>::<function_name>` | `<Code Smell or SOLID Principle>` | `<Refactoring Action>` | `<int>` | `<int>` | `100% Green` |

### Required Columns:
1. **Target Element:** File path and qualified function or class name (e.g. `src/services/billing.py::calculate_invoice`).
2. **Code Smell / Principle:** Specific defect or design principle addressed (e.g., Deep Nesting, SRP Violation, Direct Infrastructure Coupling / DIP).
3. **Technique Applied:** Concrete transformation used (e.g., Guard Clauses, Extract Helper Methods, Dependency Injection via Protocol).
4. **$V(G)$ Before:** McCabe cyclomatic complexity metric before refactoring (from `ast_complexity.py`).
5. **$V(G)$ After:** McCabe cyclomatic complexity metric after refactoring (must be $\le 10$).
6. **Test Suite Status:** Explicit confirmation of test pass status (e.g. `100% Green (42/42 tests passing)`).

---

## 3. Pre-Handover Quality Gate Checklist

Ensure all questions are answered affirmatively before issuing the Phase 3 handover recommendation:

- [ ] Did all unit tests pass before touching any production code?
- [ ] Were all modifications strictly confined to files in `git diff develop...HEAD`?
- [ ] Does `ast_complexity.py` report $V(G) \le 10$ for every modified Python function?
- [ ] Did `ast_complexity.py` return zero $O(N^2)$ nested loop warnings?
- [ ] Were all unit test files kept 100% untouched without altering assertions?
- [ ] Did all unit tests pass green on the final refactored code?
- [ ] Was the Living DoD updated in `01-concepcao/dod-[slug].md`?
- [ ] Were intermediate micro-checkpoints squashed via `git reset --soft` (Mode 3)?
