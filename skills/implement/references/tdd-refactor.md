# Operational Guide: TDD Blue Phase / Micro-Refactor (`references/tdd-refactor.md`)

This guide defines the standards and boundaries for the **Blue Phase (Micro-Refactor)** executed at the end of each TDD batch during `/implement`.

---

## 1. Micro-Refactoring vs. Macro-Refactoring

Understanding the separation of concerns between `/implement` and `/refactor` is critical:

| Dimension | Micro-Refactor (Blue Phase in `/implement`) | Macro-Refactor (Phase 3 in `/refactor`) |
|---|---|---|
| **Execution Timing** | Immediately after the batch tests turn GREEN | At feature conclusion (Phase 3) |
| **Scope** | Strictly the local class, method, or helper created in the current batch | Entire feature changeset (`git diff develop...HEAD`) |
| **Objective** | Clean names, extract private helpers, remove magic constants | Cross-module SOLID, architectural boundary verification, AST cyclomatic complexity $V(G) \le 10$ |
| **Tooling** | Immediate test execution (`pytest tests/unit/`) | AST complexity scanner (`ast_complexity.py`), Clean Architecture linter |

---

## 2. Invariant Safety Rules

1. **100% Green Test Invariant:**
   - Refactoring is permitted **only** when all unit tests for the current batch are passing green.
   - Never refactor on a broken or failing test suite.
2. **Immediate Test Re-execution:**
   - Execute the unit test suite after each atomic refactoring step:
     ```bash
     python -m pytest tests/unit/test_<module_name>.py -v
     ```
   - If a refactoring edit breaks a test, revert the edit immediately.
3. **Strict Batch Boundary:**
   - Do NOT touch code outside the active batch. If you notice structural debt in pre-existing files, note it for Phase 3 (`/refactor`).

---

## 3. The 5 Micro-Refactoring Transformations

### Transformation 1: Expressive & Domain-Rich Renaming
Replace cryptic or abbreviated names with clear domain terminology:
- **Before:** `def proc(d, u): ...`
- **After:** `def process_withdrawal_transaction(amount: Decimal, account_id: str) -> TransactionResult: ...`

### Transformation 2: Extract Private Helper Methods
Prevent functions from exceeding 20–25 lines from birth. Break monolithic routines into private helper methods:
- **Before:**
  ```python
  def execute(self, order: Order) -> None:
      # 30 lines checking inventory, calculating discounts, computing taxes, formatting payload
      ...
  ```
- **After:**
  ```python
  def execute(self, order: Order) -> OrderConfirmation:
      self._validate_stock_availability(order)
      discount = self._compute_applicable_discount(order)
      final_amount = self._apply_taxes(order.subtotal - discount)
      return self._dispatch_payment(order.id, final_amount)
  ```

### Transformation 3: Promote Magic Literals to Named Constants
Replace hardcoded strings and numbers with class or module-level constants:
- **Before:** `if user.score > 750: fee = amount * 0.015`
- **After:**
  ```python
  PREMIUM_CREDIT_SCORE_THRESHOLD: int = 750
  PREMIUM_PROCESSING_FEE_RATE: Decimal = Decimal("0.015")

  if user.score >= PREMIUM_CREDIT_SCORE_THRESHOLD:
      fee = amount * PREMIUM_PROCESSING_FEE_RATE
  ```

### Transformation 4: Guard Clauses & Early Returns
Eliminate nested `if-else` pyramids:
- **Before:**
  ```python
  def execute(self, request):
      if request.is_authenticated:
          if request.has_permission:
              if not request.is_expired:
                  return self.process(request)
              else:
                  raise ExpiredError()
          else:
              raise PermissionDeniedError()
      else:
          raise AuthenticationRequiredError()
  ```
- **After:**
  ```python
  def execute(self, request: ServiceRequest) -> ServiceResponse:
      if not request.is_authenticated:
          raise AuthenticationRequiredError("Authentication required.")
      if not request.has_permission:
          raise PermissionDeniedError("Permission denied.")
      if request.is_expired:
          raise ExpiredError("Request token expired.")
      
      return self.process(request)
  ```

### Transformation 5: Local Duplication Elimination
If two methods within the newly created class duplicate serialization, validation, or error mapping, extract a common private helper method.

---

## 4. Verification Checklist

Before closing the Blue Phase and committing the batch:
- [ ] All method and variable names accurately reflect the business domain.
- [ ] No functions exceed 25 lines of executable logic.
- [ ] No magic numbers or hardcoded string literals remain.
- [ ] Deep nesting replaced with guard clauses.
- [ ] Batch unit tests executed in terminal and 100% green.
