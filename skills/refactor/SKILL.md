---
name: refactor
description: Executes macro-refactoring across the entire feature git diff (develop...HEAD) using a context-isolated SOLID subagent while enforcing AST cyclomatic complexity (V(G) <= 10) and the SDD 2.0 Drift Gate.
---

# Skill: Consolidation Macro-Refactoring (`/refactor` — SDD 2.0)

Phase 3 feature consolidation (`git diff develop...HEAD`), AST complexity ($V(G) \le 10$, [`ast_complexity.py`](./scripts/ast_complexity.py)), SDD 2.0 Drift Gate ([`check_sdd_drift.py`](../implement/scripts/check_sdd_drift.py)), and isolated subagent (`solid-refactorer`). Scope: `01-concepcao/{sdd,dod}-[slug].md`.

## Execution Pipeline

| Step / Phase | Actor | Technical Directive & Invariants | Refs & Tools |
| :--- | :--- | :--- | :--- |
| **1. DISCOVERY** | Orchestrator | Entry Gate: run `pytest` (100% green) + coverage check (`pytest --cov=<target_files> --cov-report=term-missing` when available; warn if < 80% on $V(G)>10$ targets); diff `develop...HEAD --name-only`. Run baseline AST & SDD drift scans. | [`ast_complexity.py`](./scripts/ast_complexity.py), [`check_sdd_drift.py`](../implement/scripts/check_sdd_drift.py) |
| **2. MAP** | Orchestrator | Map smells ($V(G) > 10$, SRP > 25 lines, DIP, $O(N^2)$) to `task_list.md` (`RequestFeedback: true`). | [`solid-catalog.md`](./references/solid-catalog.md) |
| **3. REFACTOR** | `solid-refactorer` (`inherit`) | Apply SOLID (Zero New External Dependencies — stdlib/manifest only; `MaxIterations: 2` per target circuit breaker), preserve public signatures, verify $V(G) \le 10$, zero SDD drift, green pytest. Safe rollback on Double-Strike: `git stash push -u -m "antigravity-refactor-safety-rollback" && git reset --hard <target_start_hash>`. | [`refactor-subagents.md`](./references/refactor-subagents.md) |
| **4. VERIFY** | Orchestrator | Run Test Tampering Gate (`git diff --exit-code <PHASE_START_HASH>...HEAD -- tests/` — ABORT & revert if non-zero); full AST & SDD drift scans; compile Refactoring Evidence Matrix; update `dod-[slug].md`. | [`refactor-dod.md`](./references/refactor-dod.md), [`refactor-report-template.md`](./resources/refactor-report-template.md) |
| **5. SQUASH** | Orchestrator | Mode 3 Squash commit (`git reset --soft <HASH>`). Walkthrough: [`refactor-example.md`](./examples/refactor-example.md). | [`refactor-git.md`](./references/refactor-git.md) |

## Exit Gates

| Gate | Command / Action | Pass Criteria |
| :--- | :--- | :--- |
| **Tampering Gate** | `git diff --exit-code <PHASE_START_HASH>...HEAD -- tests/` | Exit 0 (zero test files modified/weakened; ABORT & revert if non-zero). |
| **Full AST** | `python skills/refactor/scripts/ast_complexity.py <FILES> --threshold 10` | Exit 0 (mandatory blocking), $V(G) \le 10$, zero $O(N^2)$. |
| **Full Drift** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <FILES> --check-files --pivots 02-auditorias/pivots-[slug].md` | Exit 0 (100% SDD parity). |
| **Regression** | `python -m pytest tests/unit/ -v` | 100% green tests. |
| **DoD & Git** | Update `dod-[slug].md` Section 3; execute Mode 3 Phase Squash. | Single Phase 3 commit. |
