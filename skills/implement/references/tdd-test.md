# TDD Red Phase Specification (`references/tdd-test.md`)

## 1. Invariants & Standards
- **Test-First:** Zero live I/O. Fixtures in `conftest.py`. Ref: [`test-template.py`](../resources/test-template.py).
- **Mocks:** `create_autospec(IPort, instance=True)`. Never mock entities/VOs.
- **Naming:** `tests/unit/test_<mod>.py`; `test_should_<outcome>_when_<cond>()`.

## 2. 6-Category Coverage Matrix

| Category | Directive & Assertion Pattern |
| :--- | :--- |
| **1. Happy** | Nominal flow; assert DTO outputs & `assert_called_once()`. |
| **2. Edge** | `@pytest.mark.parametrize` on `0`, `<0`, `""`, `None`. |
| **3. Domain** | `with pytest.raises(ExpectedDomainError):` |
| **4. Resil** | Port failure: `mock.side_effect = TimeoutError()` -> fallback. |
| **5. Concurr** | Race: `ThreadPoolExecutor(max_workers=20)` -> exact state. |
| **6. Sec** | Masking: secret not in `caplog`, `"***REDACTED***"`. |

## 3. AAA & Concurrency Snippet

```python
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import create_autospec

def test_should_register_user_when_valid():
    repo = create_autospec(IUserRepository, instance=True)
    repo.find_by_email.return_value = None
    assert RegisterUserUseCase(repo).execute(UserInput("a@b.com")).status == "CREATED"

def test_should_prevent_double_spend_race():
    svc = WithdrawService(InMemoryAccountRepo(Account("a1", 100)))
    with ThreadPoolExecutor(20) as ex:
        res = [f.result() for f in [ex.submit(svc.withdraw, "a1", 100) for _ in range(20)]]
    assert sum(r.is_success for r in res) == 1
```