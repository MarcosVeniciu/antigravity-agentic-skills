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
| `feature/{{FEATURE_SLUG_1}}` | `[[sdd-{{FEATURE_SLUG_1}}]]` | {{FEATURE_DESC_1}} | {{DOD_STATUS_AND_EVIDENCE}} |
| `feature/{{FEATURE_SLUG_2}}` | `[[sdd-{{FEATURE_SLUG_2}}]]` | {{FEATURE_DESC_2}} | {{DOD_STATUS_AND_EVIDENCE}} |

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

> **Verification Policy:** Every row below MUST cite actual verification outputs from the current release execution or explicit links to `02-auditorias/audit-*` reports (or `N/A - Verified in Pre-Merge Gate 2`). Never claim static compliance without executed evidence.

| Audit Domain | Validation Criteria | Primary Evidence / Tool | Conformity Status & Evidence |
|:---|:---|:---|:---|
| **Living DoD Gate** | 100% verified across all bundled features | [`../references/release-checklist.md`](../references/release-checklist.md) | `{{DOD_STATUS_AND_EVIDENCE}}` |
| **Integration Suite** | 100% green pass with zero regressions | `python -m pytest tests/integration/ -v` | `{{INTEGRATION_TEST_LOG_EVIDENCE}}` |
| **Domain & Security Audits** | 5-Domain Review & Sinks signed off | `02-auditorias/audit-*.md` / `scan_sinks.py` | `{{SECURITY_AUDIT_REPORT_LINKS}}` |
| **Automated Release Validation** | Validated via release gate script | [`../scripts/validate_release.py`](../scripts/validate_release.py) | `{{DOD_STATUS_AND_EVIDENCE}}` |
| **Manifest Synchronization** | Orchestrated in accordance with manifest | [`../SKILL.md`](../SKILL.md) | `{{SECURITY_AUDIT_REPORT_LINKS}}` |

### Release Findings & Residual Risk Disclosures

#### 📌 Release Finding 1: {{RELEASE_FINDING_TITLE_OR_NONE}}
* **Target / Component:** `{{COMPONENT_OR_MODULE}}`
* **Condition / Residual Risk:** {{RISK_OR_LIMITATION_DESCRIPTION_OR_NONE}}
* **Approved Mitigation / Follow-up:** {{MITIGATION_PLAN_OR_NA}}

---
*Release orchestrated via Google Antigravity Agentic Workflows (`/release`).*
