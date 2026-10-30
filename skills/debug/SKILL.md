---
name: debug
description: Conducts forensic root cause analysis (5 Whys framework) for critical crashes, exceptions, and complex runtime failures using context-isolated probing subagents.
---

# Skill: Forensic Bug Investigation & Root Cause Analysis (`/debug`)

| Invariant | Operational Rule |
| :--- | :--- |
| **Mandatory RCA Gate** | Zero production edits before `root_cause_analysis.md` approval ([`rca-template.md`](./resources/rca-template.md), `RequestFeedback: true`). |
| **Context Isolation** | Probing executed exclusively in `forensic-prober` (`Model: "inherit"`). Scratch files purged before return. |
| **Mandatory 5th Why** | Why #5 must identify why automated tests failed to catch defect before runtime. |
| **Deterministic Red** | Deterministic failing regression test required before applying any fix. |

---

## Execution Pipeline

| Step | Actor | Technical Directive & Invariants | CLI / Refs |
| :--- | :--- | :--- | :--- |
| **1. Triage** | `Orchestrator` | Ingest stack trace, environment, and `/test-fix` Double-Strike context ($H_1, H_2$ falsified). Query `02-auditorias/pivots-[slug].md`. | `git status --short`<br>[`debug-methodology.md`](./references/debug-methodology.md) |
| **2. Probing & 5 Whys** | `forensic-prober` | Formulate competing $H_1, H_2$. Execute isolated probing tests or MRE; falsify vs confirm; purge scratch. Complete 5 Whys. | [`debug-subagents.md`](./references/debug-subagents.md) |
| **3. RCA Gate** | `Orchestrator` | Generate `root_cause_analysis.md` (Option A vs B, regression design). Submit with `RequestFeedback: true`. Wait for approval. | [`rca-template.md`](./resources/rca-template.md) |
| **4. Fix & Verify** | `Orchestrator` | Confirm regression fails (Red). Apply fix (Green). Run SDD Drift Gate, commit, archive to Obsidian. Trace: [`debug-example.md`](./examples/debug-example.md). | [`debug-methodology.md`](./references/debug-methodology.md) |

```bash
python -m pytest tests/regression/ -v
python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <files> --batch --pivots 02-auditorias/pivots-[slug].md
git add <files> && git commit -m "fix(debug): resolve [defect] with regression test"
```
