# Protocol: Obsidian Vault Architecture & Note Governance

Specifications for vault hierarchy, schemas, and patches per [`../resources/note-template.md`](../resources/note-template.md).

## 1. Directory Hierarchy

| Directory | Scope | Invariants |
| :--- | :--- | :--- |
| `00-core-rules/` | ADRs, `domain-glossary.md`, `conventions.md` | SSOT for rules; inspect `backlinks`. |
| `01-concepcao/` | `bdd-*`, `sdd-*`, `epic-*`, `dod-*` | Conception, contracts, DAG, Living DoD. |
| `02-auditorias/` | `audit-*`, `pivots-*` | Domain audits, TDD drift logs. |
| `03-releases/` | `changelog-v*`, `release-manifest.md` | SemVer release notes, tagged manifests. |
| `04-templates/` | Reference templates | [`note-template.md`](../resources/note-template.md). |

---

## 2. Note Schemas & Patch Protocol (`vault_patch`)

| Note Type | Path | Required Fields | Permitted `status` |
| :--- | :--- | :--- | :--- |
| **ADR** | `00-core-rules/adrs/` | `type: adr`, `feature`, `project`, `date`, `description`, `status`, `tags` | `proposed`, `accepted`, `superseded`, `rejected` |
| **Domain Rule** | `00-core-rules/` | `type: domain_rule`, `feature: global`, `project`, `date`, `description`, `status`, `tags` | `active`, `superseded` |
| **Pivot** | `02-auditorias/` | `type: pivot`, `feature`, `project`, `date`, `description`, `status`, `tags` | `in_progress`, `resolved` |
| **Living DoD** | `01-concepcao/` | `type: dod`, `feature`, `project`, `date`, `description`, `status`, `tags` | `active`, `completed` |

| Patch Target | Directive & Invariant |
| :--- | :--- |
| `heading` | `targetType: "heading"`, `heading: "<title>"`, `action: "append" \| "replace"`. |
| `frontmatter` | `targetType: "frontmatter"`, key-value delta to merge. Preserve `---`. |
