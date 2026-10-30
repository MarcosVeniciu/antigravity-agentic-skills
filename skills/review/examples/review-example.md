# Review Walkthrough (`examples/review-example.md`)

Trace of `/review --fix` on `feature/checkout-flow`. References: [`review-performance.md`](../references/review-performance.md), [`review-resilience.md`](../references/review-resilience.md).

## 1. Entry Gate

```bash
git --no-pager diff develop...HEAD --name-only
python -m pytest tests/unit/ -v
```

## 2. 5-Domain Audit & Mode B Remediation Trace

| Domain | Finding & Tool | Fix (Mode B) | Verification & Commit |
| :--- | :--- | :--- | :--- |
| **Arch** | `ARC-01`: HTTP in domain. `check_arch_boundaries.py` | Injected `IPaymentGateway`. | Linter PASS.<br>`git commit -m "checkpoint(review): arch"` |
| **Security** | `SEC-01`: `shell=True` in `routes.py`. `scan_sinks.py` | `subprocess.run(["receipt", id], check=True)`. | Scanner PASS.<br>`git commit -m "checkpoint(review): sec"` |
| **Quality** | `QLT-01`: $V(G) = 13$. `ast_complexity.py` | Guard clauses, helper, set. New $V(G)=4$. | AST PASS.<br>`git commit -m "checkpoint(review): qlt"` |
| **Perf** | `PRF-01`: N+1 queries. | Batched query with `IN (...)` & dict. | 51 -> 2 queries.<br>`git commit -m "checkpoint(review): perf"` |
| **Resilience** | `RES-01`: Missing timeout/idempotency. | Added `httpx.Timeout` & `Idempotency-Key`. | Tests PASS.<br>`git commit -m "checkpoint(review): res"` |

## 3. Verification & Phase Squash Commit

```bash
python -m pytest tests/ -v
# Mark 5 audit items [x] in 01-concepcao/dod-checkout-flow.md
git commit -m "audit(review): specialized domain audits completed for checkout-flow"
```
