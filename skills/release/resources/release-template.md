# Release Notes - `v{{VERSION}}` ({{DATE}})

## Release Overview

| Metric | Details |
|:---|:---|
| **Release Version** | `v{{VERSION}}` |
| **Previous Version** | `v{{PREVIOUS_VERSION}}` |
| **Release Date** | {{DATE}} |
| **SemVer Increment** | {{BUMP_TYPE}} (MAJOR \| MINOR \| PATCH) |
| **Release Branch** | `release/v{{VERSION}}` |
| **Target Tag** | `v{{VERSION}}` |

---

## Features Included in Release Bundle

| Feature Branch | Obsidian SDD Reference | Description | Living DoD Status |
|:---|:---|:---|:---|
| `feature/{{FEATURE_SLUG_1}}` | `[[sdd-{{FEATURE_SLUG_1}}]]` | {{FEATURE_DESC_1}} | [x] 100% Complete |
| `feature/{{FEATURE_SLUG_2}}` | `[[sdd-{{FEATURE_SLUG_2}}]]` | {{FEATURE_DESC_2}} | [x] 100% Complete |

---

## Changes by Category

### New Features (`feat:`)
- `[feat]`: {{FEAT_DESCRIPTION_1}} (ref: `[[sdd-{{FEATURE_SLUG_1}}]]`)
- `[feat]`: {{FEAT_DESCRIPTION_2}} (ref: `[[sdd-{{FEATURE_SLUG_2}}]]`)

### Bug Fixes (`fix:`)
- `[fix]`: {{FIX_DESCRIPTION_1}}
- `[fix]`: {{FIX_DESCRIPTION_2}}

### Performance Improvements & Refactoring (`perf:`, `refactor:`)
- `[perf]`: {{PERF_DESCRIPTION_1}}
- `[refactor]`: {{REFACTOR_DESCRIPTION_1}}

### Breaking Changes & Deprecations (`BREAKING CHANGE:`)
- `[BREAKING]`: {{BREAKING_DESCRIPTION_OR_NONE}}
  - **Migration Path:** {{MIGRATION_INSTRUCTIONS_OR_NA}}

### Infrastructure, Tooling & Dependencies (`infra:`, `chore:`)
- `[infra]`: {{INFRA_DESCRIPTION_OR_NONE}}

---

## Quality & Verification Audit Sign-Off

- [x] **Living DoD Gate:** 100% verified across all bundled features via [`../references/release-checklist.md`](../references/release-checklist.md).
- [x] **Integration Suite:** Test suite passed green (`python -m pytest tests/integration/ -v`).
- [x] **Static Security & Boundaries:** Clean architecture and secret containment scans confirmed.
- [x] **Automated Release Validation:** Validated via [`../scripts/validate_release.py`](../scripts/validate_release.py).
- [x] **Manifest Synchronization:** Orchestrated in accordance with [`../SKILL.md`](../SKILL.md).

---
*Release orchestrated via Google Antigravity Agentic Workflows (`/release`).*
