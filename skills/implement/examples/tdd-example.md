# Real-World Walkthrough: TDD Cycle Example (`examples/tdd-example.md`)

This example demonstrates the execution of a complete SDD 2.0 TDD cycle for **Batch 1: Payment Processing** within the feature `payment-gateway`.

---

## 1. Batch Definition & Explicit Acceptance Criteria (`task_list.md`)

```markdown
## Batch 1: Core Payment Processing Use Case
- **Target Files:**
  - Test: `tests/unit/test_payment_service.py`
  - Code: `src/payment/service.py`
- **Acceptance Criteria (SDD & BDD Contract Mapping):**
  - [ ] **SDD Contracts Implemented:** `IPaymentGateway` (`charge`), `PaymentRequest`, `PaymentResult`, `PaymentDeniedError`, and `ProcessPaymentUseCase` (`execute`).
  - [ ] **BDD Scenarios Covered in Unit Tests:**
    - `@happy-path`: Scenario "Process valid payment when funds are available" -> `test_should_process_payment_successfully_when_funds_are_available()`
    - `@unhappy-path`: Scenario "Reject payment when gateway denies charge" -> `test_should_raise_payment_denied_error_when_gateway_declines()`
  - [ ] **Quality & Isolation Invariants:** 100% AAA unit tests passing with `create_autospec`, methods <= 25 lines, and `check_sdd_drift.py --batch` exit code 0.
- **Execution Steps:**
  - [ ] Write unit tests `tests/unit/test_payment_service.py` (Red)
  - [ ] Implement `src/payment/service.py` (Green)
  - [ ] Micro-refactor local service methods (Blue)
  - [ ] Run batch SDD Drift Gate (`check_sdd_drift.py --batch`)
  - [ ] Update Living DoD timeline & commit batch checkpoint
```

---

## 2. Red Phase: AAA Unit Tests (`batch-implementer`)

The isolated `batch-implementer` subagent creates `tests/unit/test_payment_service.py` covering the mapped BDD scenarios:

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

## 3. Green Phase: Minimal Production Code (`batch-implementer`)

`batch-implementer` creates `src/payment/service.py` with minimal typed code to satisfy the test and SDD contracts:

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, Dict, Any

class PaymentDeniedError(Exception):
    pass

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

## 4. Blue Phase & Batch Drift Check (`batch-implementer`)

With tests 100% green, `batch-implementer` applies micro-refactoring and runs the Batch Drift Check:

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

### Terminal Output (Green Invariant & Drift Gate Verification)
```text
$ python -m pytest tests/unit/test_payment_service.py -v
============================= test session starts =============================
tests/unit/test_payment_service.py::test_should_process_payment_successfully PASSED [100%]
============================== 1 passed in 0.05s ===============================

$ python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-payment-gateway.md src/payment/service.py --batch
✅ [PASS] Zero unauthorized specification drift detected between SDD and code.
```

---

## 5. Orchestrator Governance & Step 3 `flash_lite` Acceptance Verification

1. **Update Living DoD & `task_list.md`:** Mark Batch 1 criteria `[x]` and append entry to `01-concepcao/dod-payment-gateway.md`.
2. **Git Checkpoint:**
   ```bash
   git add tests/unit/test_payment_service.py src/payment/service.py
   git commit -m "checkpoint(implement): batch 1 - payment processing use case"
   ```
3. **Step 3 Post-TDD Verification (`goldfish-drift-auditor` on `Model: "flash_lite"`):**
   - Full `check_sdd_drift.py` passes with exit code 0.
   - `goldfish-drift-auditor` (`Model: "flash_lite"`, read-only) confirms `[PASS]: 100%_ACCEPTANCE_VERIFIED`.
