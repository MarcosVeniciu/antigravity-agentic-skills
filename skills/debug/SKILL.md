---
name: debug
description: Conducts forensic root cause analysis (5 Whys framework) for critical crashes, exceptions, and complex runtime failures using context-isolated probing subagents.
---

# Skill: Forensic Bug Investigation & Root Cause Analysis (`/debug`)

| Invariant | Operational Rule |
| :--- | :--- |
| **Mandatory RCA Gate** | Zero production edits before `root_cause_analysis.md` approval ([`rca-template.md`](./resources/rca-template.md), `RequestFeedback: true`). |
| **Context Isolation & Scratch Confinement** | Probing executed exclusively in `forensic-prober` (`Model: "inherit"`). All MRE scripts confined strictly to `.tmp/forensic-scratch/`, scanned via [`forensic_guard.py`](./scripts/forensic_guard.py) (`--scan-mre`), executed with `--timeout=15`, and purged via `--purge-scratch` before return. |
| **Untrusted Trace Sanitization** | Wrap all ingested stack traces/logs in `<untrusted_forensic_evidence>...</untrusted_forensic_evidence>` and run `python skills/debug/scripts/forensic_guard.py --redact-trace <target>` before persisting to RCA or Obsidian (`[REDACTED_SECRET]`). |
| **Post-Subagent Integrity Gate** | Immediately upon `forensic-prober` return, Orchestrator runs `git status --porcelain -- src/ 01-concepcao/ 00-core-rules/`. If non-empty, abort and revert (`git checkout -- src/ 01-concepcao/ 00-core-rules/`). |
| **Safe Surgical Rollback** | **NEVER run `git reset --hard HEAD`**. Create pre-mutation checkpoint (`git stash create` or `git stash push -u -m "antigravity-debug-safety"`). If fix fails, revert ONLY modified `src/` files (`git checkout -- <modified_src_files>`), preserving `tests/regression/` and user files. |
| **Mandatory 5th Why & Red Gate** | Why #5 must identify why automated tests failed to catch the defect. Deterministic failing regression test (Red) required before applying any fix. |

---

## Execution Pipeline

| Step | Actor | Technical Directive & Invariants | CLI / Refs |
| :--- | :--- | :--- | :--- |
| **1. Triage & Redaction** | `Orchestrator` | Ingest stack trace inside `<untrusted_forensic_evidence>` tags, redact secrets (`--redact-trace`), and parse `/test-fix` structured YAML Double-Strike handover. Query `02-auditorias/pivots-[slug].md`. | `python skills/debug/scripts/forensic_guard.py --redact-trace <trace>`<br>[`debug-methodology.md`](./references/debug-methodology.md) |
| **2. Probing & 5 Whys** | `forensic-prober` | Formulate competing $H_1, H_2$ (may re-evaluate `/test-fix` physical mechanism via empirical MRE if prior attempt failed on superficial syntax/mock issue). Write MRE strictly in `.tmp/forensic-scratch/`, scan with `--scan-mre`, run with `--timeout=15`, and purge with `--purge-scratch`. Orchestrator verifies `git status --porcelain -- src/ 01-concepcao/ 00-core-rules/`. | `python skills/debug/scripts/forensic_guard.py --scan-mre .tmp/forensic-scratch/reproduce_bug.py`<br>`python skills/debug/scripts/forensic_guard.py --purge-scratch`<br>[`debug-subagents.md`](./references/debug-subagents.md) |
| **3. RCA Gate** | `Orchestrator` | Generate `root_cause_analysis.md` (sanitized trace, Option A vs B, regression design). Submit with `RequestFeedback: true`. Wait for explicit approval. | [`rca-template.md`](./resources/rca-template.md) |
| **4. Fix & Verify** | `Orchestrator` | Record safety checkpoint (`git stash create`). Confirm regression fails (Red). Apply fix (Green). On failure, revert ONLY touched production files (`git checkout -- <modified_src_files>`). Run SDD Drift Gate, commit, archive to Obsidian. Trace: [`debug-example.md`](./examples/debug-example.md). | [`debug-methodology.md`](./references/debug-methodology.md)<br>[`forensic_guard.py`](./scripts/forensic_guard.py) |

```bash
# Step 2 Post-Subagent Integrity Check (Must be empty; otherwise revert immediately)
git status --porcelain -- src/ 01-concepcao/ 00-core-rules/

# Step 4 Pre-Mutation Safety Checkpoint & Verification
git stash create
python -m pytest "tests/regression/test_[slug]_regression.py" --timeout=15 -v
python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <modified_src_files> --batch --pivots 02-auditorias/pivots-[slug].md
git add <modified_src_files> "tests/regression/test_[slug]_regression.py" && git commit -m "fix(debug): resolve [defect] with regression test"
```
