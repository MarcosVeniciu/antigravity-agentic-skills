# Operational Guide: Batch Acceptance Criteria, Subagents & Drift Gate (`references/tdd-subagents.md`)

This guide governs the **SDD 2.0 (Elephant & Goldfish)** multi-agent execution model during Phase 2 (`/implement`), defining explicit **Batch Acceptance Criteria** in `task_list.md`, isolating TDD execution per batch via `batch-implementer`, enforcing AST contract parity via `check_sdd_drift.py`, and running a fast post-TDD verification pass via `goldfish-drift-auditor` (`Model: "flash_lite"`).

---

## 1. Explicit Batch Acceptance Criteria in `task_list.md` (Step 1)

A subagent cannot know whether its work truly satisfies the business and architectural specification if `task_list.md` only contains generic tasks like *"Write tests"* and *"Implement service"*.

In Step 1, the Orchestrator **MUST** structure every batch in `task_list.md` with explicit, verifiable **Acceptance Criteria (`Critérios de Aceite`)** linking the batch directly to `01-concepcao/bdd-[slug].md` and `01-concepcao/sdd-[slug].md`:

```markdown
## Batch [N]: [Batch Title]
- **Target Files:**
  - Test: `tests/unit/test_<module>.py`
  - Code: `src/<layer>/<module>.py`
- **Acceptance Criteria (SDD & BDD Contract Mapping):**
  - [ ] **SDD Contracts Implemented:** Classes/Interfaces `<ClassA>`, `<IPortB>` with public methods `<method_1>(...) -> <ReturnType>` and exceptions `<DomainError>`.
  - [ ] **BDD Scenarios Covered in Unit Tests:**
    - `@happy-path`: Scenario "<Scenario Title 1>" -> tested by `test_should_<outcome>_when_<condition>()`
    - `@unhappy-path` / `@security` / `@concurrency`: Scenario "<Scenario Title 2>" -> tested by `test_should_raise_<error>_when_<condition>()`
  - [ ] **Quality & Isolation Invariants:** 100% AAA unit tests passing green with `create_autospec`, zero live I/O, methods <= 25 lines, and `check_sdd_drift.py --batch` exit code 0.
- **Execution Steps:**
  - [ ] 1. RED: Write failing AAA unit tests covering all mapped BDD scenarios
  - [ ] 2. GREEN: Implement minimal typed production code for mapped SDD contracts
  - [ ] 3. BLUE: Apply local micro-refactoring (guard clauses, named constants, private helpers)
  - [ ] 4. DRIFT: Pass `check_sdd_drift.py --batch`
  - [ ] 5. GOV: Update Living DoD timeline and record Git checkpoint
```

---

## 2. Step 2 Subagent: `batch-implementer` (1 Invocation per Batch)

Define `batch-implementer` once using `define_subagent` (`EnableWriteTools: true`) and invoke a fresh instance (`invoke_subagent`, `Model: "inherit"`) for each batch $N$ in `task_list.md`.

- **Configuration:**
  - `Name`: `"batch-implementer"`
  - `EnableWriteTools`: `true`
  - `Model`: `"inherit"`
  - `Role`: `"TDD Batch N Implementer"`
- **SystemPrompt:**
  > *"You are a Context-Isolated TDD Batch Implementer. Read the assigned Batch N Acceptance Criteria in `task_list.md`, along with `01-concepcao/bdd-[slug].md`, `01-concepcao/sdd-[slug].md`, and prior batch files in `src/` and `tests/unit/`. Execute the strict Tri-Phase TDD loop: (1) RED Phase — write AAA unit tests with boundary `create_autospec` mocks (`skills/implement/references/tdd-test.md`) covering 100% of the BDD Scenarios mapped to Batch N and run `pytest` to confirm failure; (2) GREEN Phase — write minimal strictly typed code (`skills/implement/references/tdd-code.md`) implementing all SDD Contracts mapped to Batch N until 100% green; (3) BLUE Phase — apply local micro-refactoring (`skills/implement/references/tdd-refactor.md`) keeping methods <= 25 lines and re-run `pytest`; (4) DRIFT CHECK — run `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <batch_src_files> --batch` to verify zero contract drift. Return a concise verification table proving each Acceptance Criterion of Batch N is satisfied."*

---

## 3. The SDD 2.0 Drift Gate (`check_sdd_drift.py`)

The automated CLI validator [`scripts/check_sdd_drift.py`](../scripts/check_sdd_drift.py) compares actual AST classes, interfaces, methods, exceptions, and modified file paths against `01-concepcao/sdd-[slug].md`.

### 3.1. Per-Batch Drift Check (Inside Step 2)
Validates that all classes implemented in the current batch strictly implement the public method signatures declared in the SDD `classDiagram` and YAML contracts:
```bash
python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <batch_src_files> --batch --pivots 02-auditorias/pivots-[slug].md
```

### 3.2. Full Exit Drift Gate (Step 3)
Validates across the entire `src/` tree that **every** production class, `<<Interface>>` port, public method, and typed `*Error` / `*Exception` declared in the SDD exists in code, and that all modified production files match the *File Impact Analysis* table (or are formally authorized in `02-auditorias/pivots-[slug].md`):
```bash
python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md src/ --check-files --pivots 02-auditorias/pivots-[slug].md
```

---

## 4. Step 3 Fast Acceptance & Coverage Verifier: `goldfish-drift-auditor` (`Model: "flash_lite"`)

Because AST signature parity is already enforced deterministically by `check_sdd_drift.py` and explicit Acceptance Criteria are structured in `task_list.md`, the final post-TDD verification at Step 3 is a pure **read-only checklist and traceability audit**. Running this once at the end of Step 3 with **`Model: "flash_lite"`** delivers near-zero latency and minimal token cost while guaranteeing nothing was skipped across batches.

- **Configuration:**
  - `Name`: `"goldfish-drift-auditor"`
  - `EnableWriteTools`: `false`
  - `Model`: `"flash_lite"`
  - `Role`: `"Post-TDD Acceptance & BDD Coverage Verifier"`
- **SystemPrompt:**
  > *"You are the Post-TDD Acceptance & Coverage Verifier (Context-Zero, Read-Only, `Model: flash_lite`). Inspect `task_list.md`, `01-concepcao/bdd-[slug].md`, `01-concepcao/dod-[slug].md`, and `tests/unit/`. Verify strictly: (1) Every Batch and every Acceptance Criterion checkbox in `task_list.md` is marked `[x]` and its target files exist on disk; (2) Every `@happy-path`, `@unhappy-path`, `@security`, and `@concurrency` Gherkin scenario in `01-concepcao/bdd-[slug].md` has a corresponding `test_should_...` function in `tests/unit/` with real `assert` or `pytest.raises` statements (no empty tests or `assert True`); (3) Every completed batch is logged in the development timeline of `01-concepcao/dod-[slug].md`. Return `[PASS]: 100%_ACCEPTANCE_VERIFIED` or list exact missing items."*
