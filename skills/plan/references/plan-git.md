# Git Flow Governance Guide: Planning Phase (`plan-git`)

This guide defines branch validation, ephemeral worktree conventions, and semantic commit protocols during Phase 1 (`/plan`).

---

## 1. Phase Gate 1 Lock: Base Branch Protection

Planning or implementing features directly on shared base branches is **strictly forbidden**:
- **Blocked Base Branches:** `main`, `master`, `develop`, `production`.
- **Reason:** Developing on base branches risks polluting staging environments, causes merge collisions, and circumvents code review audits.

### Automated Validation:
Execute the cross-platform branch validator:
```bash
python skills/plan/scripts/validate_branch.py
```
- If exit code is `1`, the phase gate blocks further progress until a proper working branch is created.
- If exit code is `0`, the active branch adheres to project Git Flow standards.

---

## 2. Working Branch Conventions

All working branches must start with an accepted functional prefix:

| Prefix | Usage | Example |
|---|---|---|
| `feature/` or `feat/` | New capabilities, user-facing features | `feature/producer-registration`, `feat/auth-jwt` |
| `bugfix/` or `fix/` | Defect corrections, triage fixes | `bugfix/duplicate-email-error`, `fix/null-pointer` |
| `refactor/` | Structural code improvements | `refactor/extract-repository-port` |
| `chore/` | Tooling, build scripts, configuration | `chore/update-dependencies` |
| `docs/` | Documentation, ADR updates | `docs/architecture-overview` |

### Branch Creation Command:
```bash
git checkout -b feature/[slug]
```

---

## 3. Ephemeral Git Worktree Isolation (Optional)

When working on a feature that requires an isolated environment without affecting other local working copies:
```bash
git worktree add -b feat/[slug] ../worktrees/[slug] develop
```
- After completing work and merging back into the base branch, cleanly prune the worktree and branch:
  ```bash
  git -C <path> worktree remove ../worktrees/[slug]; git -C <path> branch -d feat/[slug]
  ```

---

## 4. Mode 3: Phase 1 Closure & Semantic Commit

At the conclusion of Phase 1, when all BDD, SDD, and DoD specifications are generated:

1. **Stage all specification artifacts:**
   ```bash
   git add 01-concepcao/
   ```
2. **Execute the standardized Phase 1 semantic commit:**
   ```bash
   git commit -m "docs(conception): BDD, SDD, and DoD specifications for [slug]"
   ```
3. **Guardrail:** Never execute `git push` without explicit user instruction.
- **Validator Script:** [`scripts/validate_branch.py`](../scripts/validate_branch.py)
