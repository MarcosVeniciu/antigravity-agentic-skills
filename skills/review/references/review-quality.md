# Operational Guide: Code Quality & AST Complexity Audit

This guide governs the audit of cyclomatic complexity, cognitive load, asymptotic algorithmic heuristics, naming clarity, and Clean Code standards across the git diff.

---

## Phase 0 — Automated AST Complexity Check (Python)

Run the AST complexity scanner against modified Python files:
```bash
python skills/review/scripts/ast_complexity.py <modified_files>
```

### Governance Rules:
- **Strict Threshold:** Every function or method must maintain cyclomatic complexity $V(G) \le 10$.
- **Scope Isolation:** The AST scanner isolates nested functions and closures, ensuring helper functions do not artificially inflate parent complexity.
- **Asymptotic Warnings:** Any warning regarding nested loops ($O(N^2)$) or linear search inside loops must be investigated for algorithmic scalability.
- **Polyglot Scope:** For JavaScript/TypeScript and Dart, evaluate complexity via native tooling (`eslint`, `dart analyze`) or manual cognitive inspection.

---

## Phase 1 — In-Depth Code Inspection (Evidence Gathering)

### 1. Complexidade Ciclomática & Carga Cognitiva
- **Ramificações Excessivas:** Map functions accumulating cascades of `if/elif/else`, nested loops, and multiple `try/except` handlers exceeding $V(G) > 10$.
- **Estrutura em Pirâmide:** Identify deep nesting (> 3 indentation levels) that obscures the happy path.
- **Falta de Cláusulas de Guarda:** Flag functions that defer execution behind deeply indented `if` blocks instead of returning early on error/boundary conditions.

### 2. Legibilidade, Nomenclatura & SOLID
- **Nomes Crípticos / Abreviações Ambíguas:** Flag single-letter variables (outside mathematical loops) or vague identifiers (`temp`, `data`, `res`, `handler`).
- **Parâmetros Booleanos de Flag:** Flag functions accepting flags like `is_admin: bool` or `process_all: bool` that split the entire body into two distinct behaviors (violating SRP).
- **Código Morto & Comentários Obsoletos:** Identify commented-out code blocks, orphaned imports, and unused private variables/methods.

---

## Phase 2 — Surgical Application & Refactoring (Mode B Only)

- **Guard Clauses (Early Return):**
  ```python
  # Before: pyramid nesting
  def process_transaction(user, tx):
      if user is not None:
          if user.is_active:
              if tx.amount > 0:
                  return execute(tx)
      return None
  
  # After: inverted guard clauses, V(G) reduced, flat indentation
  def process_transaction(user, tx):
      if user is None or not user.is_active:
          return None
      if tx.amount <= 0:
          return None
      return execute(tx)
  ```
- **Extract Method / Helper Function:** Extract cohesive logic blocks into specialized helper functions to reduce parent $V(G)$ below 10:
  ```python
  # Before: large multi-step function V(G) = 14
  def handle_order(order):
      # ... 40 lines of validation, calculation, notification ...
  
  # After: extracted cohesive sub-methods, each V(G) <= 4
  def handle_order(order):
      _validate_order_items(order)
      _apply_tiered_discounts(order)
      _notify_fulfillment(order)
  ```
- **Dictionary / Strategy Dispatcher:** Replace sprawling `if/elif/else` ladders with dictionary mapping.

---

## Phase 3 — Audit Report Format

When recording findings for `02-auditorias/audit-quality-[slug].md`, instantiate [`../resources/audit-report-template.md`](../resources/audit-report-template.md) and populate the Forensic Traceability Matrix and detailed findings:

```markdown
| ID | File & Line | Element / Function | Primary Evidence / Metric | Severity | Status & Traceability |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `QLT-01` | `src/services/billing.py:55` | `calculate_invoice` | ast_complexity.py (V(G) = 14) | Medium | 🟡 **Attention** ([see Finding 1](#-finding-1-cyclomatic-complexity)) |
```
