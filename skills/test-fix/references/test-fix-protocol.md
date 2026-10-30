# Reactive Debugger & Surgical Remediation Protocol

Specifications for bottom-up traceback triage, 1-sentence RCA per [`../resources/diagnostic-report-template.md`](../resources/diagnostic-report-template.md), and Double-Strike rollback per [`../examples/test-fix-example.md`](../examples/test-fix-example.md).

## 1. Traceback Triage & Failure Classification Matrix

| Category | Exception Classes | Primary Defect Mechanism | Surgical Remedy Directive |
| :--- | :--- | :--- | :--- |
| **Type Mismatch** | `TypeError`, `AttributeError` | `None` passed to operator, missing dataclass attribute, invalid cast. | Add null-check guard, default fallback, or explicit cast in `src/`. |
| **Logic / Calculation** | `AssertionError` | Boundary off-by-one, inverted boolean, incorrect calculation formula. | Correct comparison operator, conditional branch, or arithmetic in `src/`. |
| **Boundary / Contract** | `KeyError`, `IndexError` | Missing dict key, empty list index access, schema key drift. | Use safe access (`.get()`), check bounds, or handle missing key in `src/`. |
| **State / Lifecycle** | `ValueError`, `RuntimeError` | Illegal state transition, uninitialized resource, expired token. | Enforce state validation or initialize resource in constructor. |
| **Mock / Boundary Leak** | `InvalidSpecError`, mock errors | Unaligned mock signature, leaky fixture state, missing mock return. | Align mock specification with port (`autospec=True`); reset fixtures. |

Truncated trace: `python -m pytest <test_file> -vv --tb=short`

---

## 2. 1-Sentence RCA Formula ([`diagnostic-report-template.md`](../resources/diagnostic-report-template.md))

$$\text{[Category]}: \text{[Component/Function]} \text{ fails because } \text{[exact defect mechanism]}, \text{ causing } \text{[observed failure]}.$$

- **Valid:** `Type Mismatch: _calculate_fee in src/domain/payment.py fails because amount is None for zero-cost orders, causing a TypeError during multiplication.`
- **Invalid:** ❌ `The test failed because assertion expected True but got False.` (Symptoms only).

---

## 3. Surgical Fix Invariants & Commands

| Invariant | Directive |
| :--- | :--- |
| **Production Exclusivity** | Edits belong strictly to `src/`. Never alter test assertions to mask production defects. |
| **Test Inviolability Exception** | Only permitted test edit is fixing a proven syntactic typo or broken mock in uncommitted Red tests. |
| **Minimal Scope & API** | Modify only lines causing the failure. Maintain public interfaces, method signatures, and types. |

```bash
python -m pytest <test_file> -k <test_name> -v   # Targeted verification
python -m pytest <test_file> -v                  # Full module regression check
git add <modified_files> && git commit -m "checkpoint(test-fix): surgical fix for <desc>"
```

---

## 4. Double-Strike Rule & Escalation to `/debug`

| Attempt | Status | Action & Directives |
| :--- | :--- | :--- |
| **Attempt 1** | Strike 1 (Fail) | Analyze delta from isolated test; refine hypothesis; apply 2nd minimal edit to `src/`. |
| **Attempt 2** | Strike 2 (Fail) | **DOUBLE-STRIKE:** Abort immediately. Execute `git reset --hard HEAD && git clean -fd`. Escalate to `/debug`. |
