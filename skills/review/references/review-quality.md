# Code Quality & AST (`references/review-quality.md`)

Template: [`../resources/audit-report-template.md`](../resources/audit-report-template.md).

## 1. Automated AST Scanner CLI

| Tool | CLI Command | Target & Threshold |
| :--- | :--- | :--- |
| **AST** | `python skills/review/scripts/ast_complexity.py <modified_files>` | McCabe complexity $V(G) \le 10$ per function; flags nested loops. |

## 2. Quality Invariants & Inspection Rules

| Principle | Invariant |
| :--- | :--- |
| **Complexity** | McCabe complexity $V(G) \le 10$ across all methods. |
| **Nesting** | Flat control flow; indentation depth $\le 3$. Early guard clauses. |
| **Naming** | Domain-rich naming. Reject single-letter or vague (`data`, `res`) names. |
| **Flags** | Prohibit boolean parameter branching; split into SRP functions. |
| **Dead Code** | Zero dead code, unused imports, or orphaned variables. |

## 3. Surgical Refactoring Patterns (Mode B)

```python
def process(user, tx):
    if not user or not user.is_active or tx.amount <= 0: return None
    return DISPATCHER.get(tx.type, default_handler)(tx)
```

## 4. Forensic Report (`02-auditorias/audit-quality-[slug].md`)

| ID | File:Line | Element | Evidence | Severity | Status |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `QLT-01` | `billing.py:55` | `calculate_invoice` | `ast_complexity.py` ($V(G) = 14$) | Med | 🟡 Attention |
