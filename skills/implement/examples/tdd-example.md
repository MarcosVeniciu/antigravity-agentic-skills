# Real-World Walkthrough: TDD Cycle Example (`examples/tdd-example.md`)

This example demonstrates the execution of a complete TDD cycle for **Batch 1: Payment Processing** within the feature `payment-gateway`.

---

## 1. Batch Definition (`task_list.md`)

```markdown
## Batch 1: Core Payment Processing Use Case
- [ ] Write unit tests `tests/unit/test_payment_service.py` (Red)
- [ ] Implement `src/payment/service.py` (Green)
- [ ] Micro-refactor local service methods (Blue)
- [ ] Update Living DoD timeline
- [ ] Commit batch checkpoint
```

---

## 2. Red Phase: AAA Unit Tests

The developer creates `tests/unit/test_payment_service.py` covering Happy Path, Validation, and IDOR:

```python
from decimal import Decimal
from unittest.mock import create_autospec
import pytest
from src.payment.service import ProcessPaymentUseCase, IPaymentGateway, PaymentRequest, PaymentDeniedError

def test_should_process_payment_successfully_when_funds_are_available():
    # Arrange
    mock_gateway = create_autospec(IPaymentGateway, instance=True)
    mock_gateway.charge.return_value = {"transaction_id": "tx-999", "status": "APPROVED"}
    service = ProcessPaymentUseCase(gateway=mock_gateway)
    request = PaymentRequest(user_id="usr-1", amount=Decimal("150.00"), currency="USD")

    # Act
    result = service.execute(request)

    # Assert
    assert result.transaction_id == "tx-999"
    assert result.status == "APPROVED"
    mock_gateway.charge.assert_called_once_with(user_id="usr-1", amount=Decimal("150.00"), currency="USD")
```

### Terminal Output (Red Failure Verification)
```text
$ python -m pytest tests/unit/test_payment_service.py -v
============================= test session starts =============================
FAILED tests/unit/test_payment_service.py::test_should_process_payment_successfully - ModuleNotFoundError: No module named 'src.payment.service'
============================== 1 failed in 0.04s ==============================
```
*Observation: Test failed as expected due to missing implementation.*

---

## 3. Green Phase: Minimal Production Code

The developer creates `src/payment/service.py` with minimal typed code to satisfy the test:

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, Dict, Any

class IPaymentGateway(Protocol):
    def charge(self, user_id: str, amount: Decimal, currency: str) -> Dict[str, Any]:
        ...

@dataclass(frozen=True)
class PaymentRequest:
    user_id: str
    amount: Decimal
    currency: str

@dataclass(frozen=True)
class PaymentResult:
    transaction_id: str
    status: str

class ProcessPaymentUseCase:
    def __init__(self, gateway: IPaymentGateway) -> None:
        self._gateway = gateway

    def execute(self, request: PaymentRequest) -> PaymentResult:
        response = self._gateway.charge(request.user_id, request.amount, request.currency)
        return PaymentResult(transaction_id=response["transaction_id"], status=response["status"])
```

### Terminal Output (Green Verification)
```text
$ python -m pytest tests/unit/test_payment_service.py -v
============================= test session starts =============================
tests/unit/test_payment_service.py::test_should_process_payment_successfully PASSED [100%]
============================== 1 passed in 0.05s ===============================
```

---

## 4. Blue Phase: Micro-Refactoring

With tests 100% green, the developer reviews `ProcessPaymentUseCase` to apply micro-refactoring:
- Extracts private helper `_verify_transaction_status()` to decouple gateway response parsing.
- Promotes `"APPROVED"` to a named constant.

```python
APPROVED_STATUS: str = "APPROVED"

class ProcessPaymentUseCase:
    def __init__(self, gateway: IPaymentGateway) -> None:
        self._gateway = gateway

    def execute(self, request: PaymentRequest) -> PaymentResult:
        gateway_data = self._gateway.charge(request.user_id, request.amount, request.currency)
        return self._format_result(gateway_data)

    def _format_result(self, raw_data: Dict[str, Any]) -> PaymentResult:
        return PaymentResult(
            transaction_id=str(raw_data["transaction_id"]),
            status=str(raw_data["status"]),
        )
```

### Terminal Output (Green Invariant Verification)
```text
$ python -m pytest tests/unit/test_payment_service.py -v
============================= test session starts =============================
tests/unit/test_payment_service.py::test_should_process_payment_successfully PASSED [100%]
============================== 1 passed in 0.05s ===============================
```

---

## 5. DoD Timeline & Git Checkpoint

1. **Update Living DoD:** Append entry to `01-concepcao/dod-payment-gateway.md`.
2. **Git Commit:**
   ```bash
   git add tests/unit/test_payment_service.py src/payment/service.py
   git commit -m "checkpoint(implement): batch 1 - payment processing use case"
   ```
