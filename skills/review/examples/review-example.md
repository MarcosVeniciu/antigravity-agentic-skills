# Real-World Walkthrough: 5-Domain Review Audit (`examples/review-example.md`)

This example demonstrates the execution of the `/review` skill on the branch `feature/checkout-flow` against base branch `develop`.

---

## 1. Scope Discovery & Verification Gate

```text
$ git status
On branch feature/checkout-flow
nothing to commit, working tree clean

$ git --no-pager diff develop...HEAD --name-only
src/domain/checkout.py
src/adapters/stripe_client.py
src/services/order_service.py
src/api/checkout_routes.py

$ python -m pytest tests/unit/ -v
============================= test session starts =============================
collected 28 items
tests/unit/test_checkout.py ............................                [100%]
============================== 28 passed in 0.42s ==============================
```

*Entry Gate PASSED: 28 tests passing green.*

---

## 2. Iterative 5-Domain Audits

### Domain 1: Architecture & Boundary Isolation
- **Scanner Command:**
  ```text
  $ python skills/review/scripts/check_arch_boundaries.py src/domain/checkout.py
  🔴 [VIOLATION] Architectural Leakage in Domain Layer
     📍 Location: src/domain/checkout.py:4
     🔎 Import:   import requests
     ⚠️ Reason:   Domain layer must not import external database, HTTP client, or web framework packages.
     💡 Fix:      Invert dependency: declare a domain Interface/Port and inject concrete Adapter via DI.
  ```
- **Finding:** `ARC-01`: Direct dependency on HTTP client inside `OrderCheckout` domain entity.
- **Mode B Surgical Fix:** Created `IPaymentGateway` protocol in `src/domain/checkout.py` and injected `StripePaymentClient` adapter via constructor.
- **Verification:** Boundary linter re-executed: `✅ [PASS] All scanned domain layers respect architectural boundary isolation.`
- **Checkpoint:**
  ```bash
  git add src/domain/checkout.py src/adapters/stripe_client.py
  git commit -m "checkpoint(review): fixes for architecture"
  ```

---

### Domain 2: OWASP Security & Dangerous Sinks
- **Scanner Command:**
  ```text
  $ python skills/review/scripts/scan_sinks.py src/api/checkout_routes.py
  🔴 [HIGH] SEC-CMD-01 - OS Command Injection (shell=True / exec)
     📍 Location: src/api/checkout_routes.py:38
     🔎 Snippet:  subprocess.run(f"generate_receipt --order {order_id}", shell=True)
     ⚠️ Risk:     Executing shell commands with shell=True or string concatenation enables OS command injection.
     💡 Fix:      Use argument lists without shell: subprocess.run(['cmd', arg], shell=False).
  ```
- **Finding:** `SEC-01`: Subprocess invoked with `shell=True` using untrusted route parameter `order_id`.
- **Mode B Surgical Fix:** Refactored to argument array `subprocess.run(["generate_receipt", "--order", str(order.id)], shell=False, check=True)`.
- **Verification:** Scanner re-executed: `✅ [PASS] No high or medium severity dangerous sinks detected.`
- **Checkpoint:**
  ```bash
  git add src/api/checkout_routes.py
  git commit -m "checkpoint(review): fixes for security"
  ```

---

### Domain 3: Code Quality & AST Complexity
- **Scanner Command:**
  ```text
  $ python skills/review/scripts/ast_complexity.py src/services/order_service.py
  🔴 HIGH CYCLOMATIC COMPLEXITY V(G) > 10:
     * src/services/order_service.py:45 - Function 'process_order_discounts' has V(G) = 13
  🟡 ASYMPTOTIC HEURISTIC WARNINGS:
     * src/services/order_service.py:58 [Linear Search in Loop] Found 'in' lookup inside a loop.
  ```
- **Finding:** `QLT-01`: `process_order_discounts` accumulated 4 nested `if` statements and nested loop lookup, yielding $V(G) = 13$.
- **Mode B Surgical Fix:** Applied early guard clauses and extracted `_evaluate_tier_discount` helper function. Converted coupon list to set lookup. Resulting $V(G) = 4$.
- **Verification:** Scanner re-executed: `✅ [OK] Cyclomatic complexity V(G) within limits (<= 10) for all analyzed functions.`
- **Checkpoint:**
  ```bash
  git add src/services/order_service.py
  git commit -m "checkpoint(review): fixes for quality"
  ```

---

### Domain 4: Performance & Resource Efficiency
- **Checklist Review:** Evaluated against `references/review-performance.md`.
- **Finding:** `PRF-01`: Loading line items for 50 orders in a loop executed 50 individual `db.query(Item)` queries (N+1 query pattern).
- **Mode B Surgical Fix:** Converted to batched query `db.query(Item).filter(Item.order_id.in_(order_ids)).all()` with local dictionary aggregation.
- **Verification:** Local test benchmark verified query count decreased from 51 to 2 queries.
- **Checkpoint:**
  ```bash
  git add src/services/order_service.py
  git commit -m "checkpoint(review): fixes for performance"
  ```

---

### Domain 5: Resilience & Fault Tolerance
- **Checklist Review:** Evaluated against `references/review-resilience.md`.
- **Finding:** `RES-01`: External Stripe client call instantiated `httpx.Client()` with no timeout, risking worker thread starvation on gateway latency.
- **Mode B Surgical Fix:** Added `timeout=httpx.Timeout(connect=2.0, read=8.0, write=5.0, pool=5.0)` and transmitted `Idempotency-Key` header on mutative charge requests.
- **Verification:** Tests verified timeout error propagation.
- **Checkpoint:**
  ```bash
  git add src/adapters/stripe_client.py
  git commit -m "checkpoint(review): fixes for resilience"
  ```

---

## 3. Final Integrity Validation & Handover

1. Re-run complete test suite:
   ```bash
   $ python -m pytest tests/ -v
   ============================== 28 passed in 0.44s ==============================
   ```
2. Update Living Definition of Done (`01-concepcao/dod-checkout-flow.md`):
   ```markdown
   ### Fase 4: Auditorias Especializadas (Review)
   - [x] Auditoria de Arquitetura & Acoplamento (`02-auditorias/audit-architecture-checkout-flow.md`)
   - [x] Auditoria de Segurança OWASP (`02-auditorias/audit-security-checkout-flow.md`)
   - [x] Auditoria de Qualidade de Código & AST (`02-auditorias/audit-quality-checkout-flow.md`)
   - [x] Auditoria de Performance & Recursos (`02-auditorias/audit-performance-checkout-flow.md`)
   - [x] Auditoria de Resiliência & Falhas (`02-auditorias/audit-resilience-checkout-flow.md`)
   ```
3. Phase Squash Commit:
   ```bash
   git commit -m "audit(review): specialized domain audits completed for checkout-flow"
   ```
4. Handover:
   > **[NEXT STEP]** *"Phase 4 (Audits) completed! Review findings documented in audit reports under `02-auditorias/`. Open a **NEW CHAT** and run `/docs` to finalize technical feature documentation."*
