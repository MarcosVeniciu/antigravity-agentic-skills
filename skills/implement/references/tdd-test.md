# Operational Guide: TDD Red Phase (`references/tdd-test.md`)

This guide defines the standards, patterns, and coverage requirements for authoring unit test suites during the TDD Red Phase of `/implement`.

---

## 1. Core Principles of the Red Phase

1. **Test First, Always:** Write unit test suites before writing a single line of production code.
2. **Fail for the Right Reason:** Run the newly written test to confirm that it fails specifically due to the absence of the target implementation (e.g., `ImportError`, `NotImplementedError`, or failed assertion), rather than a malformed test setup.
3. **Zero Real Physical I/O:** Unit tests must never interact with live databases, physical filesystems, or live network endpoints. Use in-memory fakes or mocks.
4. **Mock on Architectural Boundaries:** Mock only external dependencies (repositories, HTTP gateways, message queues). Never mock internal domain entities or simple value objects.

---

## 2. Canonical Arrange-Act-Assert (AAA) Pattern

Every unit test function must have its three phases explicitly separated by visual section comments:

```python
import pytest
from unittest.mock import create_autospec

def test_should_register_user_successfully_when_payload_is_valid():
    # Arrange (Prepare system state, inputs, and boundary mocks)
    mock_repo = create_autospec(IUserRepository, instance=True)
    mock_repo.find_by_email.return_value = None
    mock_repo.save.return_value = User(id="usr-101", email="user@domain.com", name="Alice")
    
    use_case = RegisterUserUseCase(repository=mock_repo)
    input_dto = RegisterUserInput(email="user@domain.com", name="Alice")

    # Act (Execute the specific behavior under test)
    result = use_case.execute(input_dto)

    # Assert (Verify outputs, state mutations, and mock interactions)
    assert result.user_id == "usr-101"
    assert result.status == "CREATED"
    mock_repo.find_by_email.assert_called_once_with("user@domain.com")
    mock_repo.save.assert_called_once()
```

---

## 3. Mocking & Isolation Standards

1. **Use `create_autospec` or `spec=Interface`:**
   - Always instantiate mocks with `create_autospec(TargetClass, instance=True)`.
   - Prevents tests from silently passing if production method signatures change or non-existent methods are called.
2. **Favor In-Memory Fakes for Complex State:**
   - When verifying repository state transitions across multiple operations, prefer an in-memory dictionary fake implementing the repository protocol over deeply nested mocks.

---

## 4. Test Suite Coverage Matrix

For every batch, the test suite must systematically cover six mandatory test categories:

| Category | Objective | Verification Pattern |
|---|---|---|
| **1. Happy Path** | Nominal business flow and return values | Direct assertion on returned DTO / entity fields |
| **2. Edge Cases** | Boundaries (0, negative, empty string, `None`, empty list) | Parametrized tests via `@pytest.mark.parametrize` |
| **3. Domain Exceptions** | Invalid state or business rule violations | `with pytest.raises(ExpectedDomainException):` |
| **4. Resilience / Timeouts** | Handling boundary mock timeouts or degradation | Assert fallback behavior or typed infrastructure errors |
| **5. Concurrency & Race Conditions** | State corruption protection under parallel execution | Multi-threaded invocation via `concurrent.futures.ThreadPoolExecutor` |
| **6. Security Boundaries** | IDOR, log masking, and safe error payloads | Assert 403 Forbidden, verify zero PII in logs via `caplog`, generic errors |

---

## 5. Concurrency & Race Condition Patterns

When testing operations that mutate shared state (e.g., account balances, voucher redemptions, stock reservations), test parallel invocations to prove atomicity:

```python
from concurrent.futures import ThreadPoolExecutor

def test_should_prevent_double_spend_under_concurrent_race():
    # Arrange
    account = Account(account_id="acc-1", balance=100)
    service = WithdrawService(repository=InMemoryAccountRepo(account))

    # Act: 20 parallel threads attempting to withdraw 100 simultaneously
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(service.withdraw, "acc-1", 100) for _ in range(20)]
        results = [f.result() for f in futures]

    # Assert: Exactly 1 transaction succeeds, 19 fail
    successes = [r for r in results if r.is_success]
    failures = [r for r in results if not r.is_success]
    assert len(successes) == 1
    assert len(failures) == 19
    assert account.balance == 0
```

---

## 6. Security Boundary Patterns

### Log Masking Verification (Zero PII in Logs)
```python
def test_should_mask_passwords_and_pii_in_audit_logs(caplog):
    # Arrange
    auth_service = AuthenticateUserService()
    credentials = {"email": "user@domain.com", "password": "SuperSecretPassword123!"}

    # Act
    auth_service.login(credentials)

    # Assert
    assert "SuperSecretPassword123!" not in caplog.text
    assert "***REDACTED***" in caplog.text
```

### Safe Error Payload (Zero Stack Trace Disclosure)
```python
def test_should_return_generic_error_payload_without_tracebacks():
    # Arrange
    mock_gateway = create_autospec(IPaymentGateway, instance=True)
    mock_gateway.charge.side_effect = RuntimeError("FATAL: Database disk failure on /dev/sda1")
    service = ProcessPaymentUseCase(gateway=mock_gateway)

    # Act
    response = service.execute(PaymentRequest(amount=50))

    # Assert
    assert response.status == "FAILED"
    assert response.error_code == "PAYMENT_PROCESSING_ERROR"
    assert "disk failure" not in response.user_message
    assert "Traceback" not in response.user_message
```

---

## 7. Naming Conventions & Layout

- **Test File Location:** `tests/unit/test_<module_name>.py`
- **Test File Colocation:** Test files mirror the package structure under `tests/unit/`.
- **Test Function Naming:** `test_should_<expected_outcome>_when_<condition>()`
  - Example: `test_should_raise_insufficient_funds_when_balance_is_low()`
- **Fixtures:** Store shared batch fixtures in `tests/unit/conftest.py`.
