# Operational Guide: Resilience & Fault Tolerance Audit

This guide governs the surgical audit and hardening of network timeouts, retries, idempotency, circuit breakers, and fallback mechanisms across the git diff.

---

## Phase 1 — In-Depth Code Inspection (Evidence Gathering)

### 1. Timeouts de Ponta a Ponta (End-to-End)
- **Ausência de Timeout Explícito:** Network calls (HTTP, gRPC, database connections, Redis, message queues) executed without explicit connect and read timeout limits.
- **Configuração Central vs Ponto de Chamada:** Verify if the shared client (`httpx.Client`, `requests.Session`, `Dio()`) configures timeouts centrally before assuming an omission at the call site.
- **Propagação de Deadlines:** Ensure distributed requests propagate remaining deadline budgets downstream to prevent processing canceled work.

### 2. Retentativas & Regra de Ouro da Idempotência
- > [!CAUTION]
  > **Golden Rule of Idempotency:** Automatic retries are **STRICTLY FORBIDDEN** on non-idempotent mutative operations (e.g. charging a card, debiting funds, sending customer emails, creating non-idempotent orders) unless a validated **Idempotency Key** is transmitted.
- **Classificação de Erros:** Retries must only trigger on transient network faults or server errors (503 Service Unavailable, 504 Gateway Timeout, connection reset). **Never retry client 4xx errors (400, 401, 403, 404, 422).**
- **Orçamento de Retentativas & Jitter:** Enforce a maximum of 2 to 3 retry attempts with exponential backoff and randomized jitter to prevent traffic amplification and the thundering herd problem.

### 3. Degradação Graciosa (Fallbacks) & Integridade
- **Segurança do Fallback:** Default fallback values or cached responses are acceptable ONLY for non-critical, decorative data (e.g. product recommendations, weather widgets).
- **Proibição de Fallback Inseguro:** **NEVER** use fallbacks for authentication decisions, authorization checks, accounting balances, or inventory availability. Critical systems must **fail closed (fail-secure)**.

### 4. Circuit Breakers & Isolamento de Falhas
- **Proteção contra Falha em Cascata:** External third-party integrations (payment gateways, notification services, LLM providers) should implement a circuit breaker to stop calling dead dependencies, freeing worker threads and connection pools.

---

## Phase 2 — Surgical Hardening (Mode B Only)

- **Configuring Explicit Client Timeouts:**
  ```python
  import httpx
  
  # Before: default indefinite timeout
  client = httpx.Client()
  
  # After: explicit connect, read, and write timeout limits
  client = httpx.Client(
      timeout=httpx.Timeout(connect=2.0, read=10.0, write=5.0, pool=5.0)
  )
  ```
- **Idempotent Retry with Exponential Backoff and Jitter:**
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
  
  @retry(
      stop=stop_after_attempt(3),
      wait=wait_exponential_jitter(initial=1, max=8),
      retry=retry_if_exception_type(TransientNetworkError),
      reraise=True
  )
  def fetch_remote_resource(resource_id: str):
      return client.get(f"/resources/{resource_id}")
  ```
- **Fail-Secure Exception Handling:**
  ```python
  # Safe: raise domain exception instead of returning silent None/False
  except PaymentGatewayUnavailable as e:
      logger.error("Payment gateway offline, aborting checkout transaction")
      raise CheckoutUnavailableException("Payment processing currently unavailable") from e
  ```

---

## Phase 3 — Audit Report Table Format

When recording findings for `02-auditorias/audit-resilience-[slug].md`, use this standardized schema:

```markdown
| ID | File / Line | Failure Scenario | Idempotent? | Severity | Confidence | Disposition | Operational Risk / Root Cause |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `RES-01` | `src/adapters/sms.py:33` | Downstream SMS Gateway Timeout | No | High | High | Confirmed | Missing timeout on HTTP client; requests can hang indefinitely |
```
