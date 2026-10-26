# Operational Guide: TDD Definition of Done (`references/tdd-dod.md`)

This guide defines the Definition of Done (DoD) verification criteria and timeline tracking for `/implement`.

---

## 1. Entry Gate Criteria (Prerequisites from `/plan`)

Before beginning implementation, verify the presence and approval of:
- [ ] Active branch is `feature/[slug]` (or `bugfix/[slug]`), never a protected branch.
- [ ] BDD specification note exists (`01-concepcao/bdd-[slug].md`).
- [ ] SDD architectural blueprint note exists (`01-concepcao/sdd-[slug].md`).
- [ ] Living DoD note initialized (`01-concepcao/dod-[slug].md`).
- [ ] Batch plan in `task_list.md` approved by the user.

---

## 2. Batch-Level DoD Checklist

A context batch is considered **DONE** only when all five criteria are fulfilled:

- [ ] **Red Phase Verified:** AAA unit tests written, cover Happy Path + Edge Cases, and fail before implementation.
- [ ] **Green Phase Verified:** Minimal typed production code written; 100% of batch unit tests pass green.
- [ ] **Blue Phase Verified:** Local micro-refactoring executed; names are semantic; methods are under 25 lines; tests remain 100% green.
- [ ] **Living DoD Timeline Updated:** Timeline entry appended to `01-concepcao/dod-[slug].md` via `@obsidian`.
- [ ] **Git Checkpoint Committed:** Atomic sub-phase commits or batch checkpoint recorded.

### Living DoD Timeline Format
Append under `## 2. Linha do Tempo de Desenvolvimento` in `01-concepcao/dod-[slug].md`:
```markdown
- **{{TIMESTAMP}}** — Lote {{BATCH_NUMBER}}: {{BATCH_TITLE}} concluído.
  - Testes: `tests/unit/test_{{COMPONENT}}.py` (100% verde)
  - Código: `src/{{PATH}}/{{COMPONENT}}.py`
  - Micro-Refatoração: Funções auxiliares extraídas, constantes promovidas.
```

---

## 3. Phase 2 Exit Gate Checklist (Implementation Completion)

Before issuing the handover to `/refactor`, verify:

- [ ] 100% of batches in `task_list.md` marked completed (`[x]`).
- [ ] Complete unit test suite executes and passes 100% in terminal (`python -m pytest tests/unit/ -v`).
- [ ] Zero unhandled architectural deviations (all deviations documented in `02-auditorias/pivots-[slug].md`).
- [ ] Mode 3 Phase Squash commit recorded with complete semantic summary.
- [ ] Mandatory handover recommendation issued:
  > **[NEXT STEP]** *"Phase 2 (TDD) completed with 100% unit tests passing green! Open a **NEW CHAT (Chat 3)** and run `/refactor` to consolidate code design with Clean Code and SOLID principles."*
