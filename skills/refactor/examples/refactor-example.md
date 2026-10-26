# Representative Output Example: Macro-Refactoring Workflow

This artifact demonstrates an end-to-end execution of Phase 3 (`/refactor`) on a newly implemented `OrderProcessingService` component across `git diff develop...HEAD`.

---

## 1. Initial State (Code Smells & High Complexity)

During Phase 2 (`/implement`), functional code was written to pass all unit tests. However, it accumulated structural debt: high cyclomatic complexity ($V(G) = 13$), deep nesting, magic numbers, tight coupling to a database client, and an $O(N^2)$ nested loop.

### Smelly Implementation (`src/services/order_service.py`):
```python
from decimal import Decimal
from typing import List, Dict, Any


class OrderService:
    def __init__(self):
        # DIP VIOLATION: Direct infrastructure coupling
        from src.infrastructure.database import PostgresConnection
        self.db = PostgresConnection()

    def process_order(self, order_data: Dict[str, Any], catalog_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        # SMELL: High cyclomatic complexity V(G) = 13, deep nesting, magic numbers
        if order_data is not None:
            if "items" in order_data and len(order_data["items"]) > 0:
                if order_data.get("status") == "PENDING":
                    subtotal = Decimal("0.00")
                    # SMELL: O(N^2) Nested loop with linear search
                    for item in order_data["items"]:
                        for catalog in catalog_items:
                            if catalog["id"] == item["catalog_id"]:
                                price = Decimal(str(catalog["price"]))
                                subtotal += price * item["quantity"]

                    discount = Decimal("0.00")
                    # SMELL: Magic numbers
                    if subtotal > Decimal("100.00"):
                        discount = subtotal * Decimal("0.10")

                    tax = (subtotal - discount) * Decimal("0.08")
                    total = subtotal - discount + tax

                    record_id = self.db.execute_insert(
                        "INSERT INTO orders (total, status) VALUES (%s, %s)",
                        (total, "CONFIRMED")
                    )

                    return {
                        "order_id": record_id,
                        "status": "CONFIRMED",
                        "total": str(total)
                    }
                else:
                    raise ValueError("Order is not in PENDING state")
            else:
                raise ValueError("Order contains no items")
        else:
            raise ValueError("Order payload cannot be None")
```

---

## 2. Baseline AST Complexity Scan

The agent executes the AST complexity scanner:
```bash
python skills/refactor/scripts/ast_complexity.py src/services/order_service.py --threshold 10
```

### Terminal Output:
```text
================================================================================
AUDIT REPORT: PYTHON AST COMPLEXITY & PERFORMANCE HEURISTICS
================================================================================
Python files analyzed: 1

HIGH CYCLOMATIC COMPLEXITY V(G) > 10:
   * src/services/order_service.py:10 - Function 'process_order' has V(G) = 13

ASYMPTOTIC HEURISTIC WARNINGS (Potential Algorithmic Bottlenecks):
   * src/services/order_service.py:18 [O(n^2) Nested Loop] Nested loop detected at depth 2. Check asymptotic complexity bounds.
================================================================================
```

---

## 3. Surgical Refactoring Transformations Applied

1. **Dependency Inversion (DIP):** Defined `OrderDatabaseProtocol` and injected it via `__init__`.
2. **Guard Clauses:** Inverted input validation checks (`if not order_data: raise ...`) to eliminate deep nesting.
3. **Named Constants:** Extracted `DISCOUNT_THRESHOLD = Decimal("100.00")`, `DISCOUNT_RATE = Decimal("0.10")`, and `TAX_RATE = Decimal("0.08")`.
4. **Extract Methods (SRP):** Split subtotal calculation, discount computation, and tax calculation into private helper methods.
5. **Algorithmic Optimization:** Converted `catalog_items` into a lookup dictionary (`{item['id']: price}`), reducing the nested loop from $O(N \cdot M)$ to $O(N + M)$.

### Refactored Implementation (`src/services/order_service.py`):
```python
from decimal import Decimal
from typing import List, Dict, Any, Protocol


class OrderDatabaseProtocol(Protocol):
    def execute_insert(self, query: str, params: tuple) -> int: ...


DISCOUNT_THRESHOLD: Decimal = Decimal("100.00")
DISCOUNT_RATE: Decimal = Decimal("0.10")
STANDARD_TAX_RATE: Decimal = Decimal("0.08")
STATUS_PENDING: str = "PENDING"
STATUS_CONFIRMED: str = "CONFIRMED"


class OrderService:
    def __init__(self, db: OrderDatabaseProtocol):
        self._db = db

    def process_order(self, order_data: Dict[str, Any], catalog_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._validate_order_payload(order_data)

        catalog_map = {cat["id"]: Decimal(str(cat["price"])) for cat in catalog_items}
        subtotal = self._compute_subtotal(order_data["items"], catalog_map)
        discount = self._compute_discount(subtotal)
        tax = self._compute_tax(subtotal - discount)
        total = subtotal - discount + tax

        order_id = self._db.execute_insert(
            "INSERT INTO orders (total, status) VALUES (%s, %s)",
            (total, STATUS_CONFIRMED)
        )

        return {
            "order_id": order_id,
            "status": STATUS_CONFIRMED,
            "total": str(total),
        }

    def _validate_order_payload(self, order_data: Dict[str, Any]) -> None:
        if not order_data:
            raise ValueError("Order payload cannot be None")
        if "items" not in order_data or not order_data["items"]:
            raise ValueError("Order contains no items")
        if order_data.get("status") != STATUS_PENDING:
            raise ValueError("Order is not in PENDING state")

    def _compute_subtotal(self, items: List[Dict[str, Any]], catalog_map: Dict[str, Decimal]) -> Decimal:
        return sum(
            catalog_map[item["catalog_id"]] * item["quantity"]
            for item in items
            if item["catalog_id"] in catalog_map
        )

    def _compute_discount(self, subtotal: Decimal) -> Decimal:
        if subtotal > DISCOUNT_THRESHOLD:
            return subtotal * DISCOUNT_RATE
        return Decimal("0.00")

    def _compute_tax(self, taxable_amount: Decimal) -> Decimal:
        return taxable_amount * STANDARD_TAX_RATE
```

---

## 4. Post-Refactoring AST & Test Verification

### 4.1. AST Complexity Re-scan:
```bash
python skills/refactor/scripts/ast_complexity.py src/services/order_service.py --threshold 10
```

```text
================================================================================
AUDIT REPORT: PYTHON AST COMPLEXITY & PERFORMANCE HEURISTICS
================================================================================
Python files analyzed: 1

[OK] Cyclomatic complexity V(G) within limits (<= 10) for all analyzed functions.
[OK] No nested loops or linear searches in loops detected.
================================================================================
```

### 4.2. Regression Test Run:
```bash
python -m pytest tests/unit/test_order_service.py -v
```

```text
============================= test session starts ==============================
collected 6 items

tests/unit/test_order_service.py::test_process_order_success PASSED      [ 16%]
tests/unit/test_order_service.py::test_process_order_with_discount PASSED [ 33%]
tests/unit/test_order_service.py::test_order_none_raises PASSED          [ 50%]
tests/unit/test_order_service.py::test_empty_items_raises PASSED         [ 66%]
tests/unit/test_order_service.py::test_non_pending_raises PASSED         [ 83%]
tests/unit/test_order_service.py::test_catalog_lookup PASSED             [100%]

============================== 6 passed in 0.04s ===============================
```

---

## 5. Refactoring Evidence Matrix

| Target Element | Code Smell / Principle | Technique Applied | $V(G)$ Before | $V(G)$ After | Test Suite Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `OrderService.__init__` | Direct Infrastructure Coupling | Dependency Inversion (`OrderDatabaseProtocol`) | 1 | 1 | 100% Green |
| `OrderService.process_order` | High Complexity & Deep Nesting | Guard Clauses & Helper Method Extraction | 13 | 1 | 100% Green |
| `OrderService.process_order` | $O(N^2)$ Nested Loop | Dictionary Hash Indexing ($O(N+M)$) | Warn | Clear | 100% Green |
| `OrderService._validate_order_payload` | Cluttered Validation in Use Case | Extracted Method with Guard Clauses | - | 4 | 100% Green |
| `OrderService._compute_subtotal` | Multi-line Loop Iteration | Extracted Generator Expression | - | 3 | 100% Green |
| `OrderService._compute_discount` | Magic Numbers | Named Constants (`DISCOUNT_THRESHOLD`) | - | 2 | 100% Green |

---

## 6. Git Flow Micro-Checkpoints and Mode 3 Phase Squash

```bash
# 1. Micro-checkpoint saved after tests pass:
git add src/services/order_service.py
git commit -m "checkpoint(refactor): OrderService - apply guard clauses, DIP, and O(N+M) lookup"

# 2. Phase 3 conclusion squash:
git reset --soft HEAD~1
git commit -m "refactor(consolidation): apply Clean Code and SOLID for order-processing

- Scope: src/services/order_service.py
- AST Complexity: V(G) reduced from 13 to <= 4 across all methods via ast_complexity.py
- Algorithmic Performance: O(N^2) loop replaced with O(N+M) dictionary lookup
- SOLID: OrderDatabaseProtocol injected via DIP; SRP validation helpers extracted
- Test Status: 100% unit tests passing green (6/6 tests passing)
- Living DoD: Phase 3 marked complete in 01-concepcao/dod-order-processing.md
- Handover: Ready for specialized domain review via /review"
```
