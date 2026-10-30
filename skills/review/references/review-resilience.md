# Resilience & Fault Tolerance (`references/review-resilience.md`)

Template: [`../resources/audit-report-template.md`](../resources/audit-report-template.md).

## 1. Resilience Invariants & Inspection Rules

| Failure Vector | Invariant Rule |
| :--- | :--- |
| **Timeouts** | Explicit connect & read timeout budgets on 100% of external calls. |
| **Idempotency** | Golden Rule of Idempotency: automatic retry forbidden without idempotency key. |
| **Retry Budgets** | Retries on transient 5xx only (never client 4xx); 2–3 attempts max with jitter. |
| **Fail-Secure** | Critical systems fail closed (fail-secure); raise domain exceptions. |
| **Circuit Breakers** | External dependencies require circuit breakers to prevent starvation. |

## 2. Surgical Hardening Patterns (Mode B)

```python
client = httpx.Client(timeout=httpx.Timeout(connect=2.0, read=10.0))
@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=8), reraise=True)
def fetch(url): return client.get(url)
except PaymentGatewayUnavailable as e:
    raise CheckoutUnavailableException("Payment unavailable") from e
```

## 3. Forensic Report (`02-auditorias/audit-resilience-[slug].md`)

| ID | File:Line | Scenario | Evidence | Severity | Status |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `RES-01` | `sms.py:33` | Downstream SMS Timeout | Missing `httpx.Timeout` | High | 🔴 Non-Compliant |
