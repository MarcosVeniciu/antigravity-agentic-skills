# Operational Guide: Performance & Resource Efficiency Audit

This guide governs the surgical audit of algorithmic complexity, data volumetrics, I/O bottlenecks, N+1 query patterns, and resource efficiency across the git diff.

---

## Operational Workload Context

Every performance observation must be evaluated against the feature's operational context:
- **Volumetria de Dados:** Expected collection sizes (dozens, thousands, millions of records).
- **Frequência de Execução:** High-throughput endpoint (1,000 req/s) vs. daily asynchronous batch job.
- **SLA de Latência:** Maximum allowable latency budget (< 50ms for synchronous APIs vs. minutes for pipelines).

---

## Phase 1 — In-Depth Code Inspection (Evidence Gathering)

### 1. Padrão N+1 & Custo de I/O Iterativo
- **Consultas em Laços:** Flag database queries (`db.query()`, `repository.find()`) or remote HTTP calls executed inside iterative loops (`for item in items`).
- **Nota Arquitetural:** The N+1 problem is primarily an **iterative I/O and network latency accumulation** defect, not necessarily an asymptotic CPU bottleneck. A single batched network round-trip is orders of magnitude faster than N round-trips.

### 2. Complexidade Assintótica ($O(N^2)$ ou Pior)
- **Laços Aninhados:** Iterating over collection $N$ and performing an inner iteration over collection $M$ without indexing.
- **Busca Linear em Laços:** Using `if item in my_list` inside an outer loop when `my_list` could be converted into a hash set or dictionary for $O(1)$ lookups.

### 3. Gerenciamento de Memória & Streaming
- **Carga Integral em Memória:** Loading entire tables (`SELECT *`) or reading massive files (`.read()`) into RAM without streaming or pagination.
- **Iteradores & Geradores:** Identify opportunities to use Python generators (`yield`) or chunked streams to keep memory consumption constant $O(1)$.

### 4. Gestão de Conexões & Recursos
- **Vazamento de Conexões:** Sockets, HTTP clients, file handles, or database sessions opened without deterministic cleanup (`with` context manager or `try/finally`).
- **Consultas sem Índices:** Unindexed filters on large tables leading to full table scans.

---

## Phase 2 — Surgical Application & Optimizations (Mode B Only)

- **Batch Queries (Eliminating N+1):**
  ```python
  # Before: N+1 queries executed inside loop
  for user in users:
      orders = db.query(Order).filter(Order.user_id == user.id).all()
  
  # After: 1 single batched query with IN clause
  user_ids = [u.id for u in users]
  all_orders = db.query(Order).filter(Order.user_id.in_(user_ids)).all()
  orders_by_user = collections.defaultdict(list)
  for o in all_orders:
      orders_by_user[o.user_id].append(o)
  ```
- **Lookup Optimization with Semantic Safety:**
  - Convert lists to `set` for $O(1)$ lookup **only if order and duplicates are irrelevant** to downstream logic.
  - If order matters, use an order-preserving dict index (`dict.fromkeys(items)`).
- **Streaming Large Files:**
  ```python
  # Safe chunked streaming
  def stream_large_file(filepath: Path, chunk_size=8192):
      with open(filepath, "rb") as f:
          while chunk := f.read(chunk_size):
              yield chunk
  ```

---

## Phase 3 — Audit Report Table Format

When recording findings for `02-auditorias/audit-performance-[slug].md`, use this standardized schema:

```markdown
| ID | File / Line | Pattern Detected | Cost Category | Severity | Confidence | Disposition | Impact / Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PRF-01` | `src/services/report.py:88` | N+1 Database Query in Loop | Network I/O Latency | High | High | Confirmed | 100 items produce 101 database round-trips; batch via IN clause |
```
