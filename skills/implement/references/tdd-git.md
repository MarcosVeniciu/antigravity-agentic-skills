# Operational Guide: TDD Git Governance (`references/tdd-git.md`)

This guide establishes the version control protocol, commit message formats, and phase squash procedures during `/implement`.

---

## 1. Commit Formatting Standards

During the execution of each batch in Phase 2, agents may use either **Atomic Sub-Phase Commits** or **Consolidated Batch Checkpoints**.

### Option A: Atomic TDD Sub-Phase Commits
When granular commit history is preferred, record an atomic commit at each step of the Red-Green-Blue cycle:
1. **Red Phase (Tests):**
   ```bash
   git add tests/unit/test_<module_name>.py
   git commit -m "test(<scope>): add unit tests for batch [N] (<feature>)"
   ```
2. **Green Phase (Implementation):**
   ```bash
   git add src/<module_path>/
   git commit -m "feat(<scope>): implement minimal logic to pass batch [N] tests"
   ```
3. **Blue Phase (Micro-Refactor):**
   ```bash
   git add src/<module_path>/
   git commit -m "refactor(<scope>): micro-refactor batch [N] class and methods"
   ```

### Option B: Consolidated Batch Checkpoints (Mode 2)
When rapid batch progression is preferred, commit a consolidated micro-checkpoint once the entire batch completes (Red + Green + Blue + DoD):
```bash
git add .
git commit -m "checkpoint(implement): batch [N] - <short_batch_description>"
```

---

## 2. Emergency Rollback Protocol (Double-Strike Rule)

If a test failure or refactoring regression cannot be resolved after two consecutive surgical attempts:
```bash
git reset --hard HEAD
```
This discards uncommitted mutations, restores the last verified green state, and keeps the repository clean.

---

## 3. Phase 2 Closure & Squash Protocol (Mode 3)

When 100% of the batches in `task_list.md` are completed, all unit tests are green, and the Living DoD is updated, intermediate checkpoints must be squashed into a single structured Phase 2 commit:

1. **Locate Phase 2 Start Commit:**
   ```bash
   git --no-pager log --oneline -n 10
   ```
   Identify `<PHASE_START_HASH>` (the commit from Phase 1 `/plan`).

2. **Execute Soft Reset:**
   ```bash
   git reset --soft <PHASE_START_HASH>
   ```
   *(All changes remain staged in the index).*

3. **Record Structured Semantic Phase Commit:**
   ```bash
   git commit -m "feat(implement): complete TDD implementation for {{FEATURE_SLUG}} (Phase 2)

   - Batches Completed: [N] context batches in task_list.md
   - Unit Test Suite: 100% green (tests/unit/test_{{FEATURE_SLUG}}.py)
   - Scope Summary:
     * Red: AAA unit tests with boundary autospec mocks
     * Green: Minimal typed production code adhering to Clean Architecture
     * Blue: Local micro-refactoring, SRP adherence, zero magic constants
   - Living DoD Updated: 01-concepcao/dod-{{FEATURE_SLUG}}.md
   - Recommended Next Step: Run /refactor for feature macro-refactoring"
   ```

---

## 4. Inviolable Version Control Rules

1. **ZERO UNAUTHORIZED PUSHES:** Never execute `git push` without explicit user instruction.
2. **PROTECTED BRANCH LOCK:** Never commit directly on `main`, `master`, `develop`, or `production`.
3. **NO BLIND STAGING:** If untracked temporary files exist, stage files selectively (`git add <file1> <file2>`) rather than using `git add .`.
