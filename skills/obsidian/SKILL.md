---
name: obsidian
description: Governs the Obsidian knowledge vault by indexing notes, creating atomic documents, executing surgical patches, and maintaining bidirectional wikilinks.
---

# Skill: Obsidian Vault Governance (`/obsidian`)

| Invariant | Operational Rule |
| :--- | :--- |
| **Surgical Patch** | Use `vault_patch`. Overwrites forbidden on existing notes. |
| **Immutability** | Never delete notes. Set `status: superseded` and `supersedes: [[note]]`. |
| **Metadata** | Frontmatter: `type`, `feature`, `project: antigravity`, `date`, `description`, `tags`. |
| **Parity** | Links must resolve to disk (`00-core-rules/`, `01-concepcao/`, etc.). |

---

## Execution Pipeline

| Step | Directive | Refs |
| :--- | :--- | :--- |
| **1. Index** | Run `search_query`. Check `backlinks` on `00-core-rules/`. | [`obsidian-protocol.md`](./references/obsidian-protocol.md) |
| **2. Create / Patch** | Create via [`note-template.md`](./resources/note-template.md) or patch via `vault_patch`. | [`note-template.md`](./resources/note-template.md), [`obsidian-protocol.md`](./references/obsidian-protocol.md) |
| **3. Validate** | Enforce schema types (`adr`, `domain_rule`, `pivot`, `sdd`, `bdd`, `dod`, `audit`, `changelog`). | [`obsidian-protocol.md`](./references/obsidian-protocol.md) |
| **4. Link** | Maintain acyclic links. | [`obsidian-example.md`](./examples/obsidian-example.md) |
