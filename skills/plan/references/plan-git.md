# Git Flow Governance: Planning Phase (`references/plan-git.md`)

Branch validation, slug sanitization, worktrees, and Mode 3 commit protocol for Phase 1.

## 1. Branch Protection, Slug Sanitization & Worktree Isolation

| Dimension | Rule & Invariants | Command / Enforcement |
| :--- | :--- | :--- |
| **Base Lock** | Base branches (`main`, `master`, `develop`, `production`) blocked. | [`validate_branch.py`](../scripts/validate_branch.py) (exit `0` passes) |
| **Prefixes & Slug Regex** | Valid prefixes: `feature/`, `feat/`, `bugfix/`, `fix/`, `hotfix/`, `refactor/`, `chore/`, `docs/`, `style/`, `test/`, `release/`.<br>**Strict Slug Regex:** `[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*` (disallows `;`, `&`, `\|`, `$`, spaces, backticks, or path traversal). | `git checkout -b feature/[slug]`<br>`python skills/plan/scripts/validate_branch.py feature/[slug]` |
| **Worktree** | Worktree add/prune using strictly validated `[slug]`. | `git worktree add -b feat/[slug] ../worktrees/[slug] develop`<br>`git -C <p> worktree remove ../worktrees/[slug]; branch -d feat/[slug]` |

## 2. Semantic Commit Protocol (Orchestrator Only)

| Step | Directive | Command |
| :--- | :--- | :--- |
| **1. Stage** | Stage conception artifacts (only `01-concepcao/` may be modified in Phase 1). | `git add 01-concepcao/` |
| **2. Commit** | Record Mode 3 commit via Main Orchestrator (`bdd-architect` and `sdd-architect` have `run_command: forbidden`). | `git commit -m "docs(conception): BDD, SDD, and DoD specifications for [slug]"` |
| **3. Guard** | Remote push blocked without explicit user approval. | Block `git push` |
