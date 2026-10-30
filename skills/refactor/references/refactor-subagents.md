# Refactoring Subagents (`references/refactor-subagents.md`)

## 1. Subagent Registry (`define_subagent` / `invoke_subagent`)

| Name | Model | Write | SystemPrompt |
| :--- | :--- | :---: | :--- |
| `solid-refactorer` | `"inherit"` | `true` | `"Role: SOLID Refactorer (Context-Isolated). Read: task_list.md, 01-concepcao/sdd-[slug].md, 02-auditorias/pivots-[slug].md, skills/refactor/references/solid-catalog.md, skills/refactor/references/refactor-git.md. Security Invariants: (1) Zero Tampering: NEVER modify, delete, or weaken any file in tests/; (2) Zero New External Dependencies: use ONLY Python stdlib (typing.Protocol, dataclasses, abc, functools) or packages already declared in the project manifest (anti-slopsquatting); (3) Circuit Breaker: MaxIterations: 2 per target. Execute per target in task_list.md: (1) Apply SOLID in src/ (preserve public signatures, immutable tests); (2) AST: python skills/refactor/scripts/ast_complexity.py <file> --threshold 10 (V(G) <= 10, exit 0); (3) Drift: python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <file> --batch --pivots 02-auditorias/pivots-[slug].md; (4) Run pytest tests/unit/; (5) On red/drift (> 2 strikes): git stash push -u -m 'antigravity-refactor-safety-rollback' && git reset --hard <target_start_hash>; (6) On green: checkpoint git, mark task_list.md [x]. Output: Refactoring Evidence Matrix."` |

## 2. Gate Tools ([`check_sdd_drift.py`](../../implement/scripts/check_sdd_drift.py), [`ast_complexity.py`](../scripts/ast_complexity.py))

| Gate | Command | Scope |
| :--- | :--- | :--- |
| **Tampering Gate** | `git diff --exit-code <PHASE_START_HASH>...HEAD -- tests/` | Verify zero test modifications in Step 4 before squash (ABORT & revert if non-zero). |
| **AST** | `python skills/refactor/scripts/ast_complexity.py <FILES> --threshold 10` | Mandatory exit 0: $V(G) \le 10$, no $O(N^2)$. |
| **Batch Drift** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <file> --batch --pivots 02-auditorias/pivots-[slug].md` | Modified signatures. |
| **Exit Drift** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <FILES> --check-files --pivots 02-auditorias/pivots-[slug].md` | 100% parity. |
