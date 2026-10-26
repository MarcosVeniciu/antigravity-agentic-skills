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

> **Audit Standard:** Aligned with ISO 19011 Quality Management Systems Audit and Pre-Release Verification standards.

| Audit Domain | Validation Criteria | Primary Evidence / Tool | Conformity Status |
|:---|:---|:---|:---:|
| **Living DoD Gate** | 100% verified across all bundled features | [`../references/release-checklist.md`](../references/release-checklist.md) | 🟢 **100% Compliant** |
| **Integration Suite** | 100% green pass with zero regressions | `python -m pytest tests/integration/ -v` | 🟢 **100% Green** |
| **Domain Audits** | 5-Domain Review signed off | `02-auditorias/audit-*.md` | 🟢 **100% Compliant** |
| **Static Security & Boundaries** | Zero dangerous sinks / clean architecture | Boundary & Sink Scanners | 🟢 **100% Compliant** |
| **Automated Release Validation** | Validated via release gate script | [`../scripts/validate_release.py`](../scripts/validate_release.py) | 🟢 **100% Compliant** |
| **Manifest Synchronization** | Orchestrated in accordance with manifest | [`../SKILL.md`](../SKILL.md) | 🟢 **100% Compliant** |

### Release Findings & Residual Risk Disclosures

#### 📌 Release Finding 1: {{RELEASE_FINDING_TITLE_OR_NONE}}
* **Target / Component:** `{{COMPONENT_OR_MODULE}}`
* **Condition / Residual Risk:** {{RISK_OR_LIMITATION_DESCRIPTION_OR_NONE}}
* **Approved Mitigation / Follow-up:** {{MITIGATION_PLAN_OR_NA}}

---
*Release orchestrated via Google Antigravity Agentic Workflows (`/release`).*
