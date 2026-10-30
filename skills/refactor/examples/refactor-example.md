# Macro-Refactoring Workflow Walkthrough (`examples/refactor-example.md`)

Walkthrough of Phase 3 macro-refactoring on `OrderService` across `git diff develop...HEAD` applying [`solid-catalog.md`](../references/solid-catalog.md).

## 1. Smelly Baseline vs. Refactored Implementation (`src/services/order_service.py`)

Baseline scan ([`ast_complexity.py`](../scripts/ast_complexity.py)): `process_order` $V(G) = 13$, $O(N^2)$ nested loop, direct DB coupling.

```python
from decimal import Decimal
from typing import List, Dict, Any, Protocol

class OrderDatabaseProtocol(Protocol):
    def execute_insert(self, query: str, params: tuple) -> int: ...

THRESHOLD: Decimal = Decimal("100.00")
RATE: Decimal = Decimal("0.10")
TAX: Decimal = Decimal("0.08")

class OrderService:
    def __init__(self, db: OrderDatabaseProtocol): self._db = db

    def process_order(self, data: Dict[str, Any], catalog: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._validate(data)
        cat = {c["id"]: Decimal(str(c["price"])) for c in catalog}
        sub = sum(cat[i["catalog_id"]] * i["quantity"] for i in data["items"] if i["catalog_id"] in cat)
        disc = sub * RATE if sub > THRESHOLD else Decimal("0.00")
        total = (sub - disc) * (Decimal("1.00") + TAX)
        oid = self._db.execute_insert("INSERT INTO orders VALUES (%s, %s)", (total, "CONFIRMED"))
        return {"order_id": oid, "status": "CONFIRMED", "total": str(total)}

    def _validate(self, data: Dict[str, Any]) -> None:
        if not data or not data.get("items") or data.get("status") != "PENDING":
            raise ValueError("Invalid order payload")
```

## 2. Evidence Matrix ([`refactor-report-template.md`](../resources/refactor-report-template.md))

`python skills/refactor/scripts/ast_complexity.py src/services/order_service.py --threshold 10` -> Exit 0.
`python -m pytest tests/unit/test_order_service.py -v` -> 100% Green.

| Target Element | Smell / Principle | Technique Applied | $V(G)$ Pre | $V(G)$ Post | Status |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `OrderService.__init__` | DIP | Inject `OrderDatabaseProtocol` | 1 | 1 | PASS |
| `OrderService.process_order` | $V(G)=13$, $O(N^2)$ | Guard Clauses, Dict Indexing | 13 | 2 | PASS |
| `OrderService._validate` | Arrow Anti-Pattern | Extracted Guard Clauses | - | 3 | PASS |

## 3. Git Checkpoint & Phase Squash

```bash
git add src/services/order_service.py && git commit -m "checkpoint(refactor): OrderService"
git reset --soft HEAD~1 && git commit -m "refactor(consolidation): Clean Code & SOLID"
```