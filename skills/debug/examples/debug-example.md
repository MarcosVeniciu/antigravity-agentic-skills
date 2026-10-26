# Concrete Walkthrough: Forensic Bug Investigation (`/debug`)

This walkthrough details a real-world forensic investigation using `/debug` to diagnose and resolve an asynchronous connection pool starvation incident that escaped unit testing.

---

## Incident Report & Symptoms

During peak load in staging, background notification workers began crashing after approximately 20 minutes of runtime with the following repeated error:

```
2026-10-26 14:22:18 [ERROR] worker.runner: Failed to process notification batch
Traceback (most recent call last):
  File "src/workers/notification_worker.py", line 47, in process_batch
    async with db_pool.acquire(timeout=5.0) as conn:
  File "src/infra/db_pool.py", line 82, in acquire
    raise PoolTimeoutError("QueuePool limit of size 10 overflow 5 reached; connection acquisition timed out after 5.0s")
infra.db_pool.PoolTimeoutError: QueuePool limit of size 10 overflow 5 reached; connection acquisition timed out after 5.0s
```

---

## Step-by-Step Investigation Walkthrough

### Step 1: Evidence Gathering & Vault Context
1. **Symptoms:** `PoolTimeoutError` after 20 minutes under concurrent load. Pool capacity is 15 connections (10 base + 5 overflow).
2. **Context Resolution:**
   - Active branch: `bugfix/notification-pool-starvation`
   - Obsidian query via `@obsidian`: Checked `00-core-rules/conventions.md` (database connections must use async context managers with bounded acquisition timeouts).
3. **Observation:** Under normal volume, the service runs without issue. Failures occur only when notification deliveries encounter upstream webhook HTTP errors.

### Step 2: Scientific Method & 5 Whys Analysis
1. **Hypotheses Formulated:**
   - **$H_1$ (Database Deadlock):** Database locks held by slow queries block connection release.
   - **$H_2$ (Connection Leak on Exception):** Exceptions during external webhook calls bypass connection release.
2. **MRE Probe:**
   Constructed `scripts/reproduce_pool_leak.py` simulating 20 notifications with 5 injected HTTP 500 errors.
   - Database locks: Zero locks detected.
   - Pool state after errors: 5 connections remained checked out permanently.
   - **Conclusion:** $H_1$ falsified; $H_2$ confirmed.
3. **The 5 Whys Chain:**
   - *Why 1:* Why did `PoolTimeoutError` crash the worker?  
     ↳ All 15 database pool connections were checked out and never returned to the pool.
   - *Why 2:* Why were connections not returned?  
     ↳ Worker tasks failed midway and terminated without executing connection return.
   - *Why 3:* Why did workers terminate without returning connections?  
     ↳ An unhandled `WebhookDeliveryError` was raised during external HTTP dispatch after the connection had already been checked out.
   - *Why 4:* Why was connection release skipped when `WebhookDeliveryError` occurred?  
     ↳ `NotificationWorker.send_one` checked out a connection via manual `conn = await pool.acquire()` without wrapping subsequent logic in a `try...finally` or async context manager.
   - *Why 5 (Mandatory Test Escape):* Why did automated unit tests miss this leak?  
     ↳ `tests/unit/test_notification_worker.py` used an `AsyncMock` for `db_pool` that returned a dummy connection object whose `.release()` method was never asserted inside exception handling paths.

### Step 3: Interactive RCA Artifact Gate
The agent generated `root_cause_analysis.md` from `resources/rca-template.md` and submitted it with `RequestFeedback: true`:

```markdown
# Root Cause Analysis (RCA) — Notification Worker Pool Starvation

**Incident Date:** 2026-10-26  
**Severity:** P2 - High  
**Component:** `src/workers/notification_worker.py`  
**Environment:** Staging  
**Status:** Awaiting Approval  

## 1. Context & Observed Symptoms
Worker tasks crashed after 20 minutes with `PoolTimeoutError: QueuePool limit of size 10 overflow 5 reached`.

## 2. 5 Whys Analysis
- **Why 1:** All 15 connections exhausted.
- **Why 2:** Connections checked out during failed notification tasks were never returned.
- **Why 3:** `WebhookDeliveryError` aborted execution before the manual `.release()` line was reached.
- **Why 4:** Manual acquisition lacked structured `try...finally` lifecycle management.
- **Why 5 (Test Escape):** Unit tests mocked the pool with a loose mock that did not track connection checkout vs release lifecycles under exception injection.

## 3. Solution Alternatives
* **Option A (Recommended):** Refactor `NotificationWorker.send_one` to use `async with db_pool.acquire_context() as conn:` ensuring guaranteed release on normal completion, exceptions, and cancellations.
* **Option B:** Add manual `try...except...finally` block calling `await db_pool.release(conn)`. (More verbose, risk of future manual checkout errors).

## 4. Verification Plan
- Create integration test `tests/integration/test_pool_leak_regression.py` running 20 failing notifications and asserting `db_pool.checkedout_count == 0`.
```

*(Execution paused until user confirmed: "Approved Option A, proceed with implementation.")*

### Step 4: Surgical Resolution, Regression Test & Knowledge Archiving

1. **Author Regression Test (`tests/integration/test_pool_leak_regression.py`):**
   ```python
   import pytest
   from unittest.mock import AsyncMock
   from src.infra.db_pool import DatabasePool
   from src.workers.notification_worker import NotificationWorker, WebhookDeliveryError

   @pytest.mark.asyncio
   async def test_connection_released_on_webhook_exception():
       # Arrange
       pool = DatabasePool(max_size=2)
       worker = NotificationWorker(db_pool=pool)
       worker.client.post = AsyncMock(side_effect=WebhookDeliveryError("Upstream 500"))

       # Act
       with pytest.raises(WebhookDeliveryError):
           await worker.send_one(notification_id="NOTIF-1")

       # Assert: Pool must have zero leaked connections
       assert pool.checkedout_count == 0, f"Leaked connections: {pool.checkedout_count}"
   ```

2. **Execute Regression Test (Confirmed Failing before fix):**
   ```bash
   python -m pytest tests/integration/test_pool_leak_regression.py -v
   ```
   Result: `FAILED: AssertionError: Leaked connections: 1`.

3. **Apply Surgical Fix in `src/workers/notification_worker.py`:**
   ```python
   # Before
   async def send_one(self, notification_id: str) -> None:
       conn = await self.db_pool.acquire()
       payload = await conn.fetch_notification(notification_id)
       await self.client.post(payload.url, payload.data)
       await conn.mark_delivered(notification_id)
       await self.db_pool.release(conn)

   # After
   async def send_one(self, notification_id: str) -> None:
       async with self.db_pool.acquire_context() as conn:
           payload = await conn.fetch_notification(notification_id)
           await self.client.post(payload.url, payload.data)
           await conn.mark_delivered(notification_id)
   ```

4. **Verify Regression Test Green:**
   ```bash
   python -m pytest tests/integration/test_pool_leak_regression.py -v
   ```
   Result: `1 passed in 0.05s`.

5. **Commit Fix & Regression Test:**
   ```bash
   git add src/workers/notification_worker.py tests/integration/test_pool_leak_regression.py
   git commit -m "fix(debug): ensure guaranteed database connection release on worker exceptions"
   ```

6. **Archive Knowledge in Obsidian Vault:**
   Appended entry to `02-auditorias/pivots-notification-worker.md` documenting the connection leak, the async context manager pattern requirement, and the new mock guideline for pool lifecycle testing.
