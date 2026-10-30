# Refactoring Git Governance (`references/refactor-git.md`)

## 1. Operational Modes (Phase 3)

| Mode | Trigger | Commands & Directives |
| :--- | :--- | :--- |
| **Discovery** | Step 1 Entry | `git --no-pager diff develop...HEAD --name-only`. Feature files only. |
| **Checkpoint (2)** | Green Pass | `git add <FILES> && git commit -m "checkpoint(refactor): [target] - [action]"` |
| **Rollback (4)** | Fail / Drift | `git stash push -u -m "antigravity-refactor-safety-rollback" && git reset --hard <target_start_hash>`. Double-Strike Rule (`MaxIterations: 2` per target). |
| **Tampering Gate** | Step 4 Verify | `git diff --exit-code <PHASE_START_HASH>...HEAD -- tests/`. Non-zero exit code -> ABORT Phase 3 and revert test modifications (`git checkout <PHASE_START_HASH> -- tests/`). |
| **Squash (3)** | Step 4.5 Closure | `git reset --soft <PHASE_START_HASH>` per protocol below. |

## 2. Phase 3 Squash Protocol (Mode 3)

```bash
git reset --soft <PHASE_START_HASH>
git commit -m "refactor(consolidation): apply Clean Code and SOLID for {{FEATURE_SLUG}}

- Scope: git diff develop...HEAD
- AST: V(G) <= 10 via ast_complexity.py; zero O(N^2)
- Architecture: Guards, helpers, constants, DIP
- Tests: 100% green; DoD: dod-{{FEATURE_SLUG}}.md"
```

## 3. Inviolable Version Control Rules

| Rule | Enforcement Directive |
| :--- | :--- |
| **Zero Push** | Forbid `git push` without explicit user instruction. |
| **Branch Safety** | Never commit directly to `main`, `master`, `develop`, or `production`. |
| **Zero Tampering** | Never modify tests or weaken assertions to force pass. |
| **Selective Staging** | Stage explicit files (`git add <file>`); never blind-stage (`git add .`). |