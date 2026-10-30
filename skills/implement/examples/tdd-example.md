# Walkthrough: TDD Cycle Example (`examples/tdd-example.md`)

Batch 1: Payment Processing (`payment-gateway`).

## 1. Batch Execution Trace Table

| Phase | Action & Verification | Status |
| :--- | :--- | :--- |
| **PLAN** | Map `IPaymentGateway`, `PaymentRequest`, `ProcessPaymentUseCase` in `task_list.md`. | Done |
| **RED** | `test_payment_service.py` with mock -> fails. | PASS |
| **GREEN** | `ProcessPaymentUseCase` in `src/payment/service.py` -> green. | PASS |
| **BLUE** | Extract `_format_result()` helper (<= 25 lines) -> green. | PASS |
| **DRIFT** | `check_sdd_drift.py --batch` exits 0. | PASS |
| **GOV** | Log in `dod-payment-gateway.md`; git checkpoint; auditor PASS. | PASS |

## 2. Minimal Code & Verification Snippets

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from unittest.mock import create_autospec

class IPaymentGateway(Protocol):
    def charge(self, uid: str, amt: Decimal, cur: str) -> dict[str, str]: ...

@dataclass(frozen=True)
class PaymentRequest: uid: str; amt: Decimal; cur: str

@dataclass(frozen=True)
class PaymentResult: tx_id: str; status: str

class ProcessPaymentUseCase:
    def __init__(self, gw: IPaymentGateway) -> None: self._gw = gw
    def execute(self, req: PaymentRequest) -> PaymentResult:
        res = self._gw.charge(req.uid, req.amt, req.cur)
        return PaymentResult(res["tx_id"], res["status"])

def test_should_process_payment_when_funds_available():
    gw = create_autospec(IPaymentGateway, instance=True)
    gw.charge.return_value = {"tx_id": "tx-999", "status": "APPROVED"}
    res = ProcessPaymentUseCase(gw).execute(PaymentRequest("u1", Decimal("150"), "USD"))
    assert res.tx_id == "tx-999" and res.status == "APPROVED"
```

```bash
python -m pytest tests/unit/test_payment_service.py -v
python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-payment-gateway.md src/payment/service.py --batch
git commit -m "checkpoint(implement): batch 1"
```