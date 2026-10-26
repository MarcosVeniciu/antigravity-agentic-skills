# Operational Reference: Refactoring Git Flow & Version Control

This guide specifies version control procedures, scope discovery commands, micro-checkpointing, rollback mechanisms, and Phase Squash consolidation for Phase 3 (`/refactor`).

---

## 1. Scope Discovery & Branch Isolation

Before analyzing or refactoring code, define the exact boundary of the feature changeset:

```bash
# Primary command: modified files against develop branch
git --no-pager diff develop...HEAD --name-only

# Fallback command: if develop branch does not exist
git --no-pager diff main...HEAD --name-only
```

### Strict Scope Boundary Rules:
1. **Feature-Only Target:** Only files returned by the `diff` command are eligible for refactoring.
2. **Untouched Legacy Immuntability:** Never refactor, reformat, or alter files outside this list, even if pre-existing code smells are detected. Scope creep outside the feature branch is strictly prohibited.

---

## 2. Mode 2: Local Micro-Checkpoints (Atomic Milestones)

Save an atomic micro-checkpoint immediately after each refactoring transformation passes the unit test suite and AST complexity verification:

```bash
git add <MODIFIED_FILES>
git commit -m "checkpoint(refactor): [target] - [action applied]"
```

### Examples:
- `checkpoint(refactor): OrderService - replace nested status checks with guard clauses`
- `checkpoint(refactor): PaymentGateway - inject PaymentProtocol via DIP`
- `checkpoint(refactor): InvoiceCalculator - extract subtotal and tax calculation helpers`

---

## 3. Mode 4: Zero-Regression Rollback & Double-Strike Rule

### Invariant Zero-Regression Rule:
If any test in the test suite fails after a refactoring change, **the refactoring change is defective**.
- **PROHIBITED:** Modifying or weakening test assertions to force tests to pass.
- **MANDATORY:** Revert the uncommitted changes immediately to the last known green checkpoint:
  ```bash
  git reset --hard HEAD
  ```

### The Double-Strike Rule:
1. **Strike 1:** An attempted refactoring breaks tests or AST complexity. Execute `git reset --hard HEAD`. Formulate an alternative, less disruptive transformation hypothesis.
2. **Strike 2:** The second attempt also breaks tests or introduces subtle behavioral divergence.
   - **Action:** Execute `git reset --hard HEAD` immediately.
   - **Resolution:** Abandon the refactoring on this specific component. Leave the working green code intact.
   - **Documentation:** Log the failure and rationale in `task_list.md`.
   - **Escalation:** If the refactoring revealed an underlying implementation bug in the feature code, mark the task and direct the user to `/test-fix`.

---

## 4. Mode 3: Phase Closure & Squash (Phase Handover)

At the conclusion of Phase 3, once all refactoring tasks in `task_list.md` are complete, AST cyclomatic complexity is $V(G) \le 10$, tests are 100% green, and the Living DoD is updated:

1. **Verify Working Tree Status:**
   ```bash
   git status --porcelain
   ```
   *(Must be completely clean with zero uncommitted changes)*.
2. **Identify Base Commit Prior to Phase 3:**
   ```bash
   git log --oneline develop..HEAD
   ```
   Identify the commit hash immediately preceding the Phase 3 `checkpoint(refactor)` commits.
3. **Execute Soft Reset (Squash):**
   ```bash
   git reset --soft <PHASE_START_HASH>
   ```
   *(All changes remain staged in the Git index while intermediate micro-checkpoints are collapsed)*.
4. **Create Structured Semantic Commit:**
   ```bash
   git commit -m "refactor(consolidation): apply Clean Code and SOLID for [slug]

   - Scope: Consolidate feature changeset on git diff develop...HEAD
   - AST Complexity: V(G) <= 10 verified for all modified functions via ast_complexity.py
   - Architecture: Guard clauses, method extraction, named constants, and DIP applied
   - Test Status: 100% unit tests passing green
   - Living DoD: Phase 3 marked in 01-concepcao/dod-[slug].md
   - Handover: Ready for specialized domain audits via /review"
   ```
5. **Verify Clean Log & State:**
   ```bash
   git status
   git log -1
   ```
