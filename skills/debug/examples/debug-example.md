# Real-World Walkthrough: Forensic Bug Investigation

Walkthrough of a `/debug` forensic diagnosis for worker connection pool starvation per [`rca-template.md`](../resources/rca-template.md) and [`debug-methodology.md`](../references/debug-methodology.md).

## 1. Investigation & 5 Whys Trace

| Phase | Finding & Technical Directive |
| :--- | :--- |
| **Incident** | Crash: QueuePool limit reached after 5.0s. Branch: `bugfix/notification-pool-starvation`. |
| **$H_1$ (Deadlock)** | Slow queries block release. Probe `scripts/reproduce_pool_leak.py`: 0 DB locks -> **Falsified**. |
| **$H_2$ (Leak)** | Exceptions skip `.release()`. Injected 5 HTTP 500s: 5 leaked conns -> **Confirmed Root Cause**. Scratch purged. |
| **5 Whys** | W1: Pool exhausted -> W2: Unreturned conns -> W3: Exception aborted before `.release()` -> W4: Lacked async context manager -> **W5 (Test Escape):** Unit tests mocked HTTP client without testing connection release on exceptions. |
| **RCA Gate** | Submit `root_cause_analysis.md` ([`rca-template.md`](../resources/rca-template.md), `RequestFeedback: true`): Option A (context manager) vs Option B (manual `try...finally`). Approved: A. |

---

## 2. Regression Test & Surgical Fix

```python
# tests/integration/test_pool_leak_regression.py (Red -> Green)
@pytest.mark.asyncio
async def test_connection_released_on_webhook_exception():
    pool = DatabasePool(max_size=2)
    worker = NotificationWorker(db_pool=pool)
    worker.client.post = AsyncMock(side_effect=WebhookDeliveryError("Upstream 500"))
    with pytest.raises(WebhookDeliveryError):
        await worker.send_one(notification_id="NOTIF-1")
    assert pool.checkedout_count == 0, f"Leaked: {pool.checkedout_count}"
```

```python
# src/workers/notification_worker.py (Surgical Fix)
async def send_one(self, notification_id: str) -> None:
-    conn = await self.db_pool.acquire()
-    ...; await self.db_pool.release(conn)
+    async with self.db_pool.acquire_context() as conn:
+        payload = await conn.fetch_notification(notification_id)
+        await self.client.post(payload.url, payload.data)
+        await conn.mark_delivered(notification_id)
```

```bash
python -m pytest tests/integration/test_pool_leak_regression.py -v  # PASSED [100%]
git add src/workers/notification_worker.py tests/integration/test_pool_leak_regression.py
git commit -m "fix(debug): ensure guaranteed database connection release on worker exceptions"
```
