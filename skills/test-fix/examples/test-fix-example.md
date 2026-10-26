# Concrete Walkthrough: Reactive Test Debugging (`/test-fix`)

This example demonstrates a complete, real-world execution of the `/test-fix` skill resolving a failing unit test in a pricing calculation engine during Phase 2 (`/implement`).

---

## Initial State & Terminal Failure

During execution of Batch 2 in `/implement`, running unit tests yielded the following failure:

```
=================================== FAILURES ===================================
________________ TestPricingService.test_calculate_tier_discount _______________

self = <tests.unit.test_pricing_service.TestPricingService object at 0x000001>

    def test_calculate_tier_discount(self):
        # Arrange
        service = PricingService(base_rate=Decimal("0.10"))
        customer = Customer(id="CUST-42", loyalty_points=None, tier="STANDARD")

        # Act
>       discount = service.calculate_tier_discount(customer, total=Decimal("150.00"))

tests/unit/test_pricing_service.py:34: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/domain/pricing_service.py:52: in calculate_tier_discount
    if customer.loyalty_points >= 1000:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    TypeError: '>=' not supported between instances of 'NoneType' and 'int'
=========================== short test summary info ============================
FAILED tests/unit/test_pricing_service.py::TestPricingService::test_calculate_tier_discount - TypeError: '>=' not supported between instances of 'NoneType' and 'int'
============================= 1 failed in 0.08s ===============================
```

---

## Execution Step-by-Step

### Step 1: Context Resolution & Ingestion
- **Branch:** `feature/loyalty-discount-engine`
- **Failing Test:** `tests/unit/test_pricing_service.py::TestPricingService::test_calculate_tier_discount`
- **Exception:** `TypeError: '>=' not supported between instances of 'NoneType' and 'int'`
- **Target File & Line:** `src/domain/pricing_service.py:52`
- **Contract Inspection:** SDD contract specifies that `Customer.loyalty_points` is optional (`Optional[int] = None`) for new accounts.

### Step 2: Traceback Triage & 1-Sentence Root Cause
- **Classification:** Type Mismatch / NoneType Boundary Failure.
- **Formulated Root Cause:**
  > **Root Cause:** Type Mismatch: `PricingService.calculate_tier_discount` in `src/domain/pricing_service.py:52` directly evaluates `customer.loyalty_points >= 1000` without checking for `None`, raising a `TypeError` when customers have uninitialized loyalty points.

### Step 3: Surgical Production Code Fix & Isolated Verification
- **Target File:** `src/domain/pricing_service.py`
- **Preserve Tests:** Do not modify `tests/unit/test_pricing_service.py`. The test validly passes a new customer with `loyalty_points=None`.

#### Code Diff Applied:
```python
# Before (src/domain/pricing_service.py:50-55)
def calculate_tier_discount(self, customer: Customer, total: Decimal) -> Decimal:
    if customer.loyalty_points >= 1000:
        return total * Decimal("0.15")
    return total * self.base_rate

# After (src/domain/pricing_service.py:50-56)
def calculate_tier_discount(self, customer: Customer, total: Decimal) -> Decimal:
    points = customer.loyalty_points or 0
    if points >= 1000:
        return total * Decimal("0.15")
    return total * self.base_rate
```

#### Isolated Test Verification:
```bash
python -m pytest tests/unit/test_pricing_service.py -k test_calculate_tier_discount -v
```

Output:
```
============================= test session starts =============================
collected 5 items / 4 deselected / 1 selected

tests/unit/test_pricing_service.py::TestPricingService::test_calculate_tier_discount PASSED [100%]

======================= 1 passed, 4 deselected in 0.04s =======================
```

#### Module-Level Regression Check:
```bash
python -m pytest tests/unit/test_pricing_service.py -v
```

Output:
```
============================= test session starts =============================
collected 5 items

tests/unit/test_pricing_service.py::TestPricingService::test_standard_rate PASSED [ 20%]
tests/unit/test_pricing_service.py::TestPricingService::test_high_tier_rate PASSED [ 40%]
tests/unit/test_pricing_service.py::TestPricingService::test_calculate_tier_discount PASSED [ 60%]
tests/unit/test_pricing_service.py::TestPricingService::test_zero_total_handled PASSED [ 80%]
tests/unit/test_pricing_service.py::TestPricingService::test_negative_total_raises_value_error PASSED [100%]

============================== 5 passed in 0.09s ==============================
```

### Step 4: Checkpoint & Handover
1. Commit the micro-checkpoint:
   ```bash
   git add src/domain/pricing_service.py
   git commit -m "checkpoint(test-fix): safely default None loyalty points to 0 in discount calculation"
   ```

2. Output Handover Notice:
   > **[NEXT STEP]** *"Surgical fix applied and verified with 100% green tests! Resume active development by running `/implement` to execute the remaining TDD batches."*
