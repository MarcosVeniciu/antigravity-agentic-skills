---
name: release
description: Orchestrates production release publication with a flash_lite DoD and SemVer subagent, enforcing 100% Living DoD verification, end-to-end integration validation, changelog synchronization, and Git Flow release finalization.
---

# Skill: Production Release & Git Flow Finalization (`/release`)

| Invariant | Operational Rule |
| :--- | :--- |
| **100% DoD Sign-Off** | Reject on any `- [ ]` across Phases 1–5 in candidate `dod-[slug].md`. Never skip empty globs. |
| **Pre-E2E Safety Gate** | Audit dependencies (`audit_dependencies.py`) and scan test fixtures (`scan_sinks.py tests/integration/`) before running `pytest`. |
| **Deterministic SemVer** | Calculate bump via [`validate_release.py`](./scripts/validate_release.py) (`--calculate-semver`). Wrap commits in `<untrusted_commit_log>` for `release-auditor` (`EnableWriteTools: false`). |
| **Orchestrator Writes** | `release-auditor` returns drafted Markdown; **Orchestrator** writes `CHANGELOG.md` & `03-releases/` via [`release-template.md`](./resources/release-template.md). |
| **Git Flow Mode 5** | Merge `release/v[VER]` to `main` (`--no-ff`), tag `v[VER]`, sync `develop`, prune branches. |

---

## Execution Pipeline

| Step | Actor | Technical Directive & Invariants | CLI / Refs |
| :--- | :--- | :--- | :--- |
| **1. DoD Audit** | `release-auditor` (`flash_lite`, Read-Only) | Verify 100% `[x]` across candidate `01-concepcao/dod-*.md`. Reject on `- [ ]`. | [`release-subagents.md`](./references/release-subagents.md), [`release-checklist.md`](./references/release-checklist.md) |
| **2. Merge & Safe E2E** | `Orchestrator` | Branch `release/v[VER]` from `develop`. Merge (`--no-ff`). Verify supply chain & scan `tests/integration/` fixtures before running integration tests. | `scan_sinks.py tests/integration/`, `python -m pytest tests/integration/ -v` |
| **3. SemVer & Sync** | `Orchestrator` + `release-auditor` (`flash_lite`, Read-Only) | Run `validate_release.py --calculate-semver develop`. Pass deterministic version + `<untrusted_commit_log>` to `release-auditor` to draft [`release-template.md`](./resources/release-template.md). **Orchestrator** writes `CHANGELOG.md` & `03-releases/changelog-v[VER].md`. | [`validate_release.py`](./scripts/validate_release.py), [`release-checklist.md`](./references/release-checklist.md) |
| **4. Finalize** | `Orchestrator` | Validate CLI (`--check-dod` fails if 0 files match). Tag `v[VER]`, merge `main` & `develop`, prune. Trace: [`release-example.md`](./examples/release-example.md). | [`validate_release.py`](./scripts/validate_release.py) |

```bash
python skills/infra/scripts/audit_dependencies.py pyproject.toml
python skills/review/scripts/scan_sinks.py tests/integration/
python skills/release/scripts/validate_release.py --calculate-semver develop --current-version v[PREV_VERSION]
python skills/release/scripts/validate_release.py --version v[VERSION] --branch release/v[VERSION] --changelog CHANGELOG.md --check-dod "01-concepcao/dod-*.md" --check-clean
```
