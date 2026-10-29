# Operational Guide: TDD Definition of Done (`references/tdd-dod.md`)

This guide defines the Definition of Done (DoD) verification criteria and timeline tracking for `/implement`.

---

## 1. Entry Gate Criteria (Prerequisites from `/plan`)

Before beginning implementation, verify the presence and approval of:
- [ ] Active branch is `feature/[slug]` (or `bugfix/[slug]`), never a protected branch.
- [ ] BDD specification note exists (`01-concepcao/bdd-[slug].md`).
- [ ] SDD architectural blueprint note exists (`01-concepcao/sdd-[slug].md`).
- [ ] Living DoD note initialized (`01-concepcao/dod-[slug].md`).
- [ ] Batch plan and explicit **Batch Acceptance Criteria** (BDD scenarios & SDD contracts mapped per batch) in `task_list.md` approved by the user.

---

## 2. Batch-Level DoD Checklist

A context batch is considered **DONE** only when all six criteria are fulfilled:

- [ ] **Red Phase Verified:** AAA unit tests written by `batch-implementer` covering all mapped BDD scenarios for the batch, failing before implementation.
- [ ] **Green Phase Verified:** Minimal typed production code written for all mapped SDD contracts; 100% of batch unit tests pass green.
- [ ] **Blue Phase Verified:** Local micro-refactoring executed; names are semantic; methods are under 25 lines; tests remain 100% green.
- [ ] **Batch Drift Check Passed:** `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <batch_src_files> --batch` exits with code 0.
- [ ] **Living DoD Timeline & Acceptance Criteria Updated:** Batch Acceptance Criteria marked `[x]` in `task_list.md` and timeline entry appended to `01-concepcao/dod-[slug].md` via `@obsidian`.
- [ ] **Git Checkpoint Committed:** Atomic sub-phase commits or batch checkpoint recorded.

### Living DoD Timeline Format
Append under `## 2. Linha do Tempo de Desenvolvimento` in `01-concepcao/dod-[slug].md`:
```markdown
- **{{TIMESTAMP}}** — Lote {{BATCH_NUMBER}}: {{BATCH_TITLE}} concluído.
  - Testes: `tests/unit/test_{{COMPONENT}}.py` (100% verde)
  - Código: `src/{{PATH}}/{{COMPONENT}}.py`
  - Micro-Refatoração: Funções auxiliares extraídas, constantes promovidas.
  - Drift Gate (Lote): 100% aderente ao SDD (`check_sdd_drift.py --batch`).
```

---

## 3. Phase 2 Exit Gate Checklist (Implementation Completion)

Before issuing the handover to `/refactor`, verify:

- [ ] 100% of batches and their Acceptance Criteria in `task_list.md` marked completed (`[x]`).
- [ ] Complete unit test suite executes and passes 100% in terminal (`python -m pytest tests/unit/ -v`).
- [ ] **Full Exit Drift Gate Passed:** `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md src/ --check-files` exits with code 0 (zero unauthorized spec drift).
- [ ] **Post-TDD Acceptance Audit Passed:** `goldfish-drift-auditor` (`Model: "flash_lite"`, read-only) confirms 100% Batch Acceptance Criteria completion and BDD scenario test parity (`[PASS]: 100%_ACCEPTANCE_VERIFIED`).
- [ ] Zero unhandled architectural deviations (all deviations documented in `02-auditorias/pivots-[slug].md`).
- [ ] Mode 3 Phase Squash commit recorded with complete semantic summary.
- [ ] Mandatory handover recommendation issued:
  > **[NEXT STEP]** *"Phase 2 (TDD) completed with 100% unit tests passing green! Open a **NEW CHAT** and run `/refactor` to consolidate code design with Clean Code and SOLID principles."*
