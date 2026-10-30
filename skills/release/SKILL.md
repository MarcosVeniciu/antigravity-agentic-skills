---
name: release
description: Orchestrates production release publication with a flash_lite DoD and SemVer subagent, enforcing 100% Living DoD verification, end-to-end integration validation, changelog synchronization, and Git Flow release finalization.
---

# Skill: Production Release & Git Flow Finalization (`/release`)

| Invariant | Operational Rule |
| :--- | :--- |
| **100% DoD Sign-Off** | Reject on any `- [ ]` across Phases 1–5 in candidate `dod-[slug].md`. |
| **Integration** | 100% green tests in `tests/integration/`. |
| **Changelog Sync** | Sync to `CHANGELOG.md` & `03-releases/` via [`release-template.md`](./resources/release-template.md). |
| **Git Flow Mode 5** | Merge `release/v[VER]` to `main` (`--no-ff`), tag `v[VER]`, sync `develop`, prune branches. |

---

## Execution Pipeline

| Step | Actor | Technical Directive & Invariants | CLI / Refs |
| :--- | :--- | :--- | :--- |
| **1. DoD Audit** | `release-auditor` (`flash_lite`) | Verify 100% `[x]` across candidate `01-concepcao/dod-*.md`. Reject on `- [ ]`. | [`release-subagents.md`](./references/release-subagents.md), [`release-checklist.md`](./references/release-checklist.md) |
| **2. Merge & E2E** | `Orchestrator` | Branch `release/v[VER]` from `develop`. Merge (`--no-ff`). Run integration tests. | `python -m pytest tests/integration/ -v` |
| **3. SemVer & Sync** | `release-auditor` (`flash_lite`) | Bump (`MAJOR > MINOR > PATCH`). Populate [`release-template.md`](./resources/release-template.md) in `CHANGELOG.md` & `03-releases/`. | [`release-checklist.md`](./references/release-checklist.md) |
| **4. Finalize** | `Orchestrator` | Validate CLI. Tag `v[VER]`, merge `main` & `develop`, prune. Trace: [`release-example.md`](./examples/release-example.md). | [`validate_release.py`](./scripts/validate_release.py) |

```bash
python skills/release/scripts/validate_release.py --version v[VERSION] --branch release/v[VERSION] --changelog CHANGELOG.md --check-dod "01-concepcao/dod-*.md" --check-clean
```
