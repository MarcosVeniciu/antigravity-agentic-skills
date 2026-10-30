# Refactoring Definition of Done (`references/refactor-dod.md`)

## 1. Phase 3 Gates

| Gate | Technical Directive | Pass Criteria |
| :--- | :--- | :--- |
| **Entry** | `python -m pytest tests/unit/ -v` (`--cov=<target_files>` coverage awareness when available) | 100% green before edits; warn if coverage < 80% on $V(G)>10$ targets. |
| **4.0 Tampering** | `git diff --exit-code <PHASE_START_HASH>...HEAD -- tests/` | Exit 0 (zero test modifications; ABORT & revert if non-zero). |
| **4.1 AST** | `python skills/refactor/scripts/ast_complexity.py <FILES> --threshold 10` | Exit 0 ($V(G) \le 10$; zero $O(N^2)$). |
| **4.2 Drift** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <FILES> --check-files --pivots 02-auditorias/pivots-[slug].md` | Exit 0 (zero SDD drift). |
| **4.3 Matrix** | Schema below; ref: [`refactor-report-template.md`](../resources/refactor-report-template.md) | All targets mapped. |
| **4.4 DoD** | Update Section 3 in `01-concepcao/dod-[slug].md`. | All items `[x]`. |
| **4.5 Squash** | Mode 3 Squash per [`refactor-git.md`](./refactor-git.md). | Single Phase 3 commit. |

## 2. Evidence Matrix Schema

| Target Element | Smell / Principle | Technique Applied | $V(G)$ Pre | $V(G)$ Post | Test Status |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `<file>::<func>` | `<Smell / Principle>` | `<Action Applied>` | `<int>` | $\le 10$ | `100% Green` |

## 3. Living DoD Template (`01-concepcao/dod-[slug].md`)

```markdown
## 3. Refactoring & Audits (Phases 3 and 4)
- [x] Entry gate: 100% unit tests green before refactoring.
- [x] Scope confined to `git diff develop...HEAD`.
- [x] Clean Code (guards, helpers, constants) & SOLID (SRP, OCP, LSP, ISP, DIP) applied.
- [x] AST complexity ($V(G) \le 10$) & asymptotic performance (zero $O(N^2)$) verified.
- [x] Zero regressions: 100% green tests with zero assertion edits.
- [x] Evidence matrix documented; Mode 3 Phase Squash executed.
```