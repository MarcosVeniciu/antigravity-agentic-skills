---
name: implement
description: Executes the iterative TDD development cycle batch by batch with context-isolated subagents, explicit batch acceptance criteria, Red-Green-Blue phases, and an SDD 2.0 Drift Gate.
---

# Skill: Iterative TDD Implementation (`/implement`)

Phase 2 batch TDD (`RED->GREEN->BLUE->DRIFT->GOV`), AST drift gate ([`check_sdd_drift.py`](./scripts/check_sdd_drift.py)), and audit (`goldfish-drift-auditor`, `flash_lite`). Scope: `01-concepcao/{bdd,sdd,dod}-[slug].md`.

## Execution Pipeline

| Step / Phase | Actor | Technical Directive & Invariants | Refs & Tools |
| :--- | :--- | :--- | :--- |
| **1. PLAN** | Orchestrator | Order batches in `task_list.md` (Domain -> Services -> Adapters). Map files, SDD contracts, and BDD tags (`RequestFeedback: true`). | [`tdd-subagents.md`](./references/tdd-subagents.md) |
| **2.1 RED** | `batch-implementer` (`inherit`) | AAA tests for BDD scenarios; boundary mocks; confirm fail. | [`tdd-test.md`](./references/tdd-test.md), [`test-template.py`](./resources/test-template.py) |
| **2.2 GREEN** | `batch-implementer` (`inherit`) | Minimal typed code (manifest/stdlib imports only); log pivots in `02-auditorias/pivots-[slug].md`; green tests. On > 2 strikes: `git stash push -u -m "antigravity-safety-rollback-strike2" && git reset --hard HEAD`. | [`tdd-code.md`](./references/tdd-code.md), [`code-template.py`](./resources/code-template.py) |
| **2.3 BLUE** | `batch-implementer` (`inherit`) | Clean code; methods <= 25 lines; green pytest (`--tb=short`). | [`tdd-refactor.md`](./references/tdd-refactor.md) |
| **2.4 DRIFT** | `batch-implementer` (`inherit`) | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <batch_files> --batch --pivots 02-auditorias/pivots-[slug].md` | [`check_sdd_drift.py`](./scripts/check_sdd_drift.py) |
| **2.5 GOV** | Orchestrator | Scope guard (`git status --porcelain` / `git diff --name-only` — abort & revert if `.env`, `.github/`, or `skills/` touched); update `task_list.md` & `dod-[slug].md`; checkpoint git. | [`tdd-dod.md`](./references/tdd-dod.md), [`tdd-git.md`](./references/tdd-git.md) |

## Step 3: Exit Gates

| Gate | Action / Command | Pass Criteria |
| :--- | :--- | :--- |
| **3.1 Suite** | `python -m pytest tests/unit/ -v --tb=short` (`--timeout=30` when available) | 100% green tests (zero live network/socket I/O). |
| **3.2 Drift** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md src/ --check-files --pivots 02-auditorias/pivots-[slug].md` | Exit 0 (100% parity; exact file/symbol pivots only). |
| **3.3 Audit** | `goldfish-drift-auditor` (`flash_lite`, read-only) per [`tdd-subagents.md`](./references/tdd-subagents.md) | `[PASS]: 100%_ACCEPTANCE_VERIFIED` (zero trivial assertions). |
| **3.4 Closure** | Mode 3 Squash per [`tdd-git.md`](./references/tdd-git.md); verify [`tdd-dod.md`](./references/tdd-dod.md). Walkthrough: [`tdd-example.md`](./examples/tdd-example.md). | Single Phase 2 commit. |
