# SOLID & Clean Code Catalog (`references/solid-catalog.md`)

## 1. Clean Code Transformations

| Pattern | Directive & Blueprint |
| :--- | :--- |
| **Guard Clauses** | Invert nested `if/else` to exit early; flatten paths.<br>`if not acc.is_active: return INACTIVE; acc.deduct(amt); return SUCCESS` |
| **Extract Helper** | Decompose methods > 25 lines into private helpers.<br>`self._validate(order); return Invoice(self._calc_subtotal(order.items))` |
| **Named Constants** | Replace magic literals (`86400`, `0.15`, `"CONFIRMED"`) with constants/enums.<br>`MAX_DAYS: int = 30; if days > MAX_DAYS: apply(...)` |

## 2. SOLID Principles Across Feature Diff

| Principle | Anti-Pattern & Remediation Directive |
| :--- | :--- |
| **SRP** | Mixed rules/I/O: Isolate domain rules in services; delegate I/O to adapters. |
| **OCP** | `if/elif` type ladders: Dispatch via strategy `dict`.<br>`STRATEGIES = {"vip": _vip_disc}; func = STRATEGIES[cust_type]; return func(amt)` |
| **LSP** | Narrowed params / `NotImplementedError`: Honor contracts; segregate protocol hierarchy. |
| **ISP** | Fat interfaces: Define lean `typing.Protocol` interfaces (`Reader`, `Writer`). |
| **DIP** | Direct instantiation (`PostgresClient()`): Constructor inject protocols.<br>`def __init__(self, repo: OrderRepoProtocol): self._repo = repo` |

## 3. AST Complexity & Performance ([`ast_complexity.py`](../scripts/ast_complexity.py))

McCabe: $V(G) = 1 + \sum(\text{decisions}) \le 10$.

| Bottleneck | Anti-Pattern | Remediation & Bound |
| :--- | :--- | :--- |
| **High $V(G)$** | Deep nesting (`if A: if B: if C:`). | Guard clauses, helper extraction. $V(G) \le 10$. |
| **$O(N^2)$ Loops** | Nested iteration over lists. | Index inner collection in `dict`. $O(N \cdot M) \to O(N + M)$. |
| **Linear Search** | `if item in list:` inside loop. | Convert list to `set` before loop. $O(N \cdot M) \to O(N + M)$. |