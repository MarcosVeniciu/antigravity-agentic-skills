# Ask Sources: Triangulation & Investigation Specification

## 1. Operational Guardrails (Strict Read-Only)

| Constraint | Enforcement | Technical Directive |
| :--- | :--- | :--- |
| **Zero Workspace Writes** | Tool Rejection | Prohibit creating, editing, or deleting codebase files. |
| **Zero Vault Writes** | Tool Rejection | Prohibit modifying Obsidian notes. |
| **Zero Mutating CLI** | Execution Guard | Prohibit package install, migrations, builds, commits. Diagnostics only (`git log`, `git status`). |
| **Zero Speculation** | Humility Gate | State gaps explicitly: *"Behavior not documented or present in codebase."* |

---

## 2. 2-Tier Source Triangulation

| Tier | Domain | Artifacts | Technical Scope |
| :--- | :--- | :--- | :--- |
| **Tier 1: Codebase Truth** | Execution behavior | `src/`, `tests/`, `pyproject.toml`, `Dockerfile`, `.env` | AST contracts, active tests, environment config. |
| **Tier 2: Obsidian Vault** | Architectural intent | `00-core-rules/`, `01-concepcao/`, `02-auditorias/`, `03-releases/` | ADRs, BDD/SDD specs, Living DoD, audit logs. |

*Invariants:* (1) Document code vs Vault contradictions explicitly. (2) Declare absent capabilities unequivocally.

---

## 3. Inquiry Routing Protocol

| Scope | Threshold | Execution Actor & Tool Sequence | Context Isolation Policy |
| :--- | :--- | :--- | :--- |
| **Direct Lookup** | 1–2 known files | `Orchestrator`: `view_file`, `grep_search` | Inspect directly in main session. |
| **Broad Survey** | > 2 files or cross-module/Vault | `research` (`flash_lite`, read-only): `grep_search`, `find_by_name`, `view_file`, search Vault `00-core-rules/`, `01-concepcao/` | Contained inside subagent sandbox. Returns strictly citation table. |

---

## 4. Formal Citation Standards

```markdown
- Code File / Lines: [auth.py#L42-L65](file:///path/to/auth.py#L42-L65)
- Manifest / Config: [pyproject.toml#L18](file:///path/to/pyproject.toml#L18)
- Obsidian Vault: [[conventions]], [[adr-002-jwt-auth]], [[sdd-user-reg]]
```
