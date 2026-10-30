# TDD Subagents & Acceptance Criteria (`references/tdd-subagents.md`)

## 1. Criteria Schema (`task_list.md`)

```markdown
## Batch [N]
- **Target:** `tests/unit/test_<mod>.py` | `src/<layer>/<mod>.py`
- **Criteria:** [ ] SDD: `<Class>`, `<m>()`, `<Err>`. [ ] BDD: `@happy-path`: `test_should_<outcome>()`; `@unhappy-path`: `test_should_raise_<err>()`. [ ] Invariants: AAA green, methods <= 25 lines, `check_sdd_drift.py --batch` exit 0.
- **Steps:** `[ ] 1.RED` | `[ ] 2.GREEN` | `[ ] 3.BLUE` | `[ ] 4.DRIFT` | `[ ] 5.GOV`
```

## 2. Subagent Registry (`define_subagent` / `invoke_subagent`)

| Name | Model | Write | SystemPrompt |
| :--- | :--- | :---: | :--- |
| `batch-implementer` | `"inherit"` | `true` | `"Role: TDD Batch N Implementer (Context-Isolated). Read: Batch N in task_list.md, 01-concepcao/{bdd,sdd}-[slug].md, src/, tests/unit/. Execute: (1) RED: AAA unit tests via create_autospec (skills/implement/references/tdd-test.md) covering 100% of Batch N BDD scenarios; run pytest to confirm failure; (2) GREEN: minimal typed code (skills/implement/references/tdd-code.md) until 100% green; (3) BLUE: micro-refactor (skills/implement/references/tdd-refactor.md) keeping methods <= 25 lines; (4) DRIFT: python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <batch_files> --batch --pivots 02-auditorias/pivots-[slug].md. Output: Verification table proving Batch N criteria."` |
| `goldfish-drift-auditor` | `"flash_lite"` | `false` | `"Role: Post-TDD Acceptance & Coverage Verifier (Context-Zero, Read-Only, flash_lite). Read: task_list.md, 01-concepcao/{bdd,dod}-[slug].md, tests/unit/. Verify strictly: (1) All Batch & Criteria checkboxes in task_list.md are [x] and target files exist on disk; (2) Every @happy-path, @unhappy-path, @security, @concurrency BDD scenario has a matching test_should_... function in tests/unit/ with real assert or pytest.raises (zero empty tests or assert True); (3) All completed batches are logged in 01-concepcao/dod-[slug].md. Output: [PASS]: 100%_ACCEPTANCE_VERIFIED or exact missing items."` |

## 3. SDD 2.0 Drift Gate CLI ([`scripts/check_sdd_drift.py`](../scripts/check_sdd_drift.py))

| Mode | Command | Scope |
| :--- | :--- | :--- |
| **Batch (2.4)** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <batch_files> --batch --pivots 02-auditorias/pivots-[slug].md` | Batch public signatures. |
| **Exit (3.2)** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md src/ --check-files --pivots 02-auditorias/pivots-[slug].md` | 100% SDD parity. |
