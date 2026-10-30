# Architecture & SDD Drift (`references/review-architecture.md`)

Standards for Phase 4. Template: [`../resources/audit-report-template.md`](../resources/audit-report-template.md).

## 1. Automated Scanners & CLI Gate

| Scanner | CLI Command | Invariant |
| :--- | :--- | :--- |
| **Boundary** | `python skills/review/scripts/check_arch_boundaries.py <modified_files>` | Exit 0. Clean domain. |
| **SDD Drift** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <modified_files> --check-files --pivots 02-auditorias/pivots-[slug].md` | Exit 0. SDD parity. |

## 2. Invariants & Inspection Rules

| Principle | Invariant |
| :--- | :--- |
| **Layering** | Domain never imports DB/ORM, HTTP, web, UI. |
| **DIP** | Require abstract `Protocol`/`ABC` injection; no direct instantiation. |
| **SDD Parity** | Match `01-concepcao/sdd-[slug].md`; pivots in `02-auditorias/pivots-[slug].md`. |
| **DTOs** | ORM models must not cross API boundaries. |
| **SRP** | Flag God Classes combining logic, DB, formatting. |

## 3. Surgical Remediation Patterns (Mode B)

```python
class CheckoutService:
    def __init__(self, gw: IPaymentGateway) -> None: self.gw = gw
order = CreateOrderDTO.from_request(req.json).to_domain()
@dataclass(frozen=True)
class OrderSnapshot: order_id: str; total: Decimal
```

## 4. Forensic Report (`02-auditorias/audit-architecture-[slug].md`)

| ID | File:Line | Principle | Evidence | Severity | Status |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `ARC-01` | `order.py:14` | Boundary | `check_arch_boundaries.py` | High | 🔴 Non-Compliant |
