# TDD Definition of Done (`references/tdd-dod.md`)

## 1. Phase 2 Gates

| Gate | Verification Directive | Pass Criteria |
| :--- | :--- | :--- |
| **Entry** | Branch `feature/[slug]`, `bdd/sdd/dod-[slug].md`, `task_list.md`. | 100% verified. |
| **3.1 Suite** | `python -m pytest tests/unit/ -v` | 100% green. |
| **3.2 Drift** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md src/ --check-files --pivots 02-auditorias/pivots-[slug].md` | Exit 0. |
| **3.3 Audit** | `goldfish-drift-auditor` (`flash_lite`) | `[PASS]: 100%_ACCEPTANCE_VERIFIED` |
| **3.4 Git** | Mode 3 Squash per [`tdd-git.md`](./tdd-git.md). | Phase 2 commit. |

## 2. Batch DoD & Timeline

| Phase | Technical Standard |
| :--- | :--- |
| **RED/GREEN** | AAA tests; minimal typed code passing tests. |
| **BLUE/DRIFT** | Methods <= 25 lines; `check_sdd_drift.py --batch` exit 0. |
| **GOV/GIT** | Task list `[x]`; append timeline below; checkpoint. |

```markdown
- **{{TIMESTAMP}}** — Lote {{BATCH_NUMBER}}: {{BATCH_TITLE}} concluído.
  - Testes: `tests/unit/test_{{COMPONENT}}.py` (100% verde) | Código: `src/{{PATH}}/{{COMPONENT}}.py`
  - Micro-Refatoração: Funções auxiliares extraídas, constantes promovidas.
  - Drift Gate (Lote): 100% aderente ao SDD (`check_sdd_drift.py --batch`).
```