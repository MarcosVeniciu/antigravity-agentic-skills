# TDD Blue Phase / Micro-Refactor Specification (`references/tdd-refactor.md`)

## 1. Micro vs. Macro Refactoring Boundaries

| Dim | Micro-Refactor (Blue in `/implement`) | Macro-Refactor (Phase 3 in `/refactor`) |
| :--- | :--- | :--- |
| **Scope** | Active batch files post-GREEN. | Feature diff (`develop...HEAD`). |
| **Target** | Local clean code: names, helpers, guards, constants. | Systemic SOLID, decoupling, AST $V(G) \le 10$. |
| **Gate** | `pytest tests/unit/test_<mod>.py -v` (100% green). | `ast_complexity.py`, linters, regression. |

## 2. The 5 Micro-Refactoring Transformations

| # | Transformation | Directive & Blueprint |
| :-: | :--- | :--- |
| **1** | **Domain Renaming** | Ubiquitous terms: `def process_withdrawal(amount: Decimal, account_id: str):` |
| **2** | **Extract Helper** | Methods > 25 lines: `self._validate(req); return self._dispatch(req)` |
| **3** | **Constants** | Module/class constants: `THRESHOLD: int = 750; if score >= THRESHOLD: ...` |
| **4** | **Guard Clauses** | Invert nested `if-else`: `if not req.is_valid: raise ValidationError()` |
| **5** | **DRY Helpers** | Deduplicate repeated logic: `self._format_payload(...)` |

## 3. Exit Checklist
- [ ] Ubiquitous names; methods <= 25 lines; zero magic constants; guard clauses flatten logic.
- [ ] Active batch tests executed and 100% green (`pytest tests/unit/test_<mod>.py -v`).