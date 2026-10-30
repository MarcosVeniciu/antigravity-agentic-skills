# Reactive Test Debugging Walkthrough

Resolution trace for a `TypeError` test failure per [`test-fix-protocol.md`](../references/test-fix-protocol.md) and [`diagnostic-report-template.md`](../resources/diagnostic-report-template.md).

## 1. Failure Trace & Triage

```text
FAILED tests/unit/test_pricing_service.py::TestPricingService::test_calculate_tier_discount
  File "src/domain/pricing_service.py", line 52, in calculate_tier_discount
    if customer.loyalty_points >= 1000:
TypeError: '>=' not supported between instances of 'NoneType' and 'int'
```

- **1-Sentence RCA** ([`diagnostic-report-template.md`](../resources/diagnostic-report-template.md)): `Type Mismatch: PricingService evaluates uninitialized loyalty_points >= 1000 without None check.`

---

## 2. Surgical Fix & Verification Trace

```python
# src/domain/pricing_service.py:50-56
def calculate_tier_discount(self, customer: Customer, total: Decimal) -> Decimal:
-    if customer.loyalty_points >= 1000:
+    points = customer.loyalty_points or 0
+    if points >= 1000:
         return total * Decimal("0.15")
     return total * self.base_rate
```

| Step | Command | Result |
| :--- | :--- | :--- |
| **Verify Target** | `python -m pytest tests/unit/test_pricing_service.py -k test_calculate_tier_discount -v` | PASSED [100%] |
| **Verify Module** | `python -m pytest tests/unit/test_pricing_service.py -v` | 5 passed [100%] |
| **Checkpoint** | `git add src/domain/pricing_service.py && git commit -m "checkpoint(test-fix): default None loyalty points"` | Committed clean |
