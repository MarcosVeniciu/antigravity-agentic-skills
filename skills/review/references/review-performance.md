# Performance & Resources (`references/review-performance.md`)

Template: [`../resources/audit-report-template.md`](../resources/audit-report-template.md).

## 1. Performance Invariants & Inspection Rules

| Pattern | Invariant Rule |
| :--- | :--- |
| **N+1 Queries** | Flag DB queries (`db.query()`) or HTTP calls in loops. Batch with `IN (...)`. |
| **Complexity** | Flag nested loops ($O(N^2)$) and linear searches in loops. Convert to hash set/dict ($O(1)$). |
| **Memory** | Prohibit bulk loading large tables (`SELECT *`) or files (`.read()`). Use chunked streams/generators. |
| **Leaks** | Sockets, HTTP clients, files, DB sessions without deterministic cleanup. Enforce `with` context. |
| **Unindexed** | Filter/join columns on high-volume tables causing full scans. Require indexed queries. |

## 2. Surgical Optimization Patterns (Mode B)

```python
orders = db.query(Order).filter(Order.user_id.in_(user_ids)).all()
allowed_ids = set(permitted_list)
valid = [i for i in items if i.id in allowed_ids]
def stream_file(p, sz=8192):
    with open(p, "rb") as f:
        while chunk := f.read(sz): yield chunk
```

## 3. Forensic Report (`02-auditorias/audit-performance-[slug].md`)

| ID | File:Line | Pattern | Evidence / Tool | Severity | Status |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `PRF-01` | `report.py:88` | N+1 Query | AST Scan / Profiler | High | 🔴 Non-Compliant |
