# Git Flow Governance: Planning Phase (`references/plan-git.md`)

Branch validation, worktrees, and Mode 3 commit protocol for Phase 1.

## 1. Branch Protection & Worktree Isolation

| Dimension | Rule & Invariants | Command / Enforcement |
| :--- | :--- | :--- |
| **Base Lock** | Base branches (`main`, `master`, `develop`, `production`) blocked. | [`validate_branch.py`](../scripts/validate_branch.py) (exit `0` passes) |
| **Prefixes** | Valid: `feature/`, `feat/`, `bugfix/`, `fix/`, `refactor/`, `chore/`, `docs/`. | `git checkout -b feature/[slug]` |
| **Worktree** | Worktree add/prune. | `git worktree add -b feat/[slug] ../worktrees/[slug] develop`<br>`git -C <p> worktree remove ../worktrees/[slug]; branch -d feat/[slug]` |

## 2. Semantic Commit Protocol

| Step | Directive | Command |
| :--- | :--- | :--- |
| **1. Stage** | Stage conception artifacts. | `git add 01-concepcao/` |
| **2. Commit** | Record Mode 3 commit. | `git commit -m "docs(conception): BDD, SDD, and DoD specifications for [slug]"` |
| **3. Guard** | Remote push blocked without approval. | Block `git push` |
