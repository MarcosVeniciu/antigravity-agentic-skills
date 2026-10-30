# Refactoring Subagents (`references/refactor-subagents.md`)

## 1. Subagent Registry (`define_subagent` / `invoke_subagent`)

| Name | Model | Write | SystemPrompt |
| :--- | :--- | :---: | :--- |
| `solid-refactorer` | `"inherit"` | `true` | `"Role: SOLID Refactorer (Context-Isolated). Read: task_list.md, 01-concepcao/sdd-[slug].md, 02-auditorias/pivots-[slug].md, skills/refactor/references/solid-catalog.md, skills/refactor/references/refactor-git.md. Execute per target in task_list.md: (1) Apply SOLID in src/ (preserve public signatures, immutable tests); (2) AST: python skills/refactor/scripts/ast_complexity.py <file> --threshold 10 (V(G) <= 10); (3) Drift: python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <file> --batch --pivots 02-auditorias/pivots-[slug].md; (4) Run pytest tests/unit/; (5) On red/drift: git reset --hard HEAD (2 strikes max); (6) On green: checkpoint git, mark task_list.md [x]. Output: Refactoring Evidence Matrix."` |

## 2. Gate Tools ([`check_sdd_drift.py`](../../implement/scripts/check_sdd_drift.py), [`ast_complexity.py`](../scripts/ast_complexity.py))

| Gate | Command | Scope |
| :--- | :--- | :--- |
| **AST** | `python skills/refactor/scripts/ast_complexity.py <FILES> --threshold 10` | $V(G) \le 10$, no $O(N^2)$. |
| **Batch Drift** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <file> --batch --pivots 02-auditorias/pivots-[slug].md` | Modified signatures. |
| **Exit Drift** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <FILES> --check-files --pivots 02-auditorias/pivots-[slug].md` | 100% parity. |
