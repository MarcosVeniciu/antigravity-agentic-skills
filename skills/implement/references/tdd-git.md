# TDD Git Governance Specification (`references/tdd-git.md`)

## 1. Commit Modes (Phase 2)

| Mode | Stage | Commands & Format |
| :--- | :--- | :--- |
| **Atomic** | Sub-phases | RED: `test(<scope>): unit tests`<br>GREEN: `feat(<scope>): minimal logic`<br>BLUE: `refactor(<scope>): clean code` |
| **Checkpoint** | Batch $N$ | `git add <batch_files> && git commit -m "checkpoint(implement): batch [N] - <desc>"` |
| **Rollback** | > 2 strikes | `git reset --hard HEAD` (restores green baseline) |

## 2. Phase 2 Closure & Squash Protocol (Mode 3)

```bash
git reset --soft <PHASE_START_HASH>
git commit -m "feat(implement): complete TDD for {{FEATURE_SLUG}} (Phase 2)

- Batches: [N] context batches in task_list.md
- Tests: 100% green (tests/unit/test_{{FEATURE_SLUG}}.py)
- Scope: Red (AAA), Green (typed), Blue (<= 25 lines)
- Living DoD: 01-concepcao/dod-{{FEATURE_SLUG}}.md"
```

## 3. Inviolable Version Control Rules

| Rule | Directive |
| :--- | :--- |
| **Zero Push** | Forbid `git push` without user instruction. |
| **Branches** | Forbid commits to `main`, `master`, `develop`, or `production`. |
| **Staging** | Explicit files (`git add <file>`); never blind-stage (`git add .`). |