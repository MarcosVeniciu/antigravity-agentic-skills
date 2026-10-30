---
name: obsidian
description: Governs the Obsidian knowledge vault by indexing notes, creating atomic documents, executing surgical patches, and maintaining bidirectional wikilinks.
---

# Skill: Obsidian Vault Governance (`/obsidian`)

| Invariant | Operational Rule |
| :--- | :--- |
| **Surgical Patch** | Use `vault_patch`. Full-file `write_file` overwrites on existing Vault notes are strictly forbidden (`[OBS-ASI03-02]`). |
| **Immutability & Non-Deletion** | Never delete notes. Terminal deletion commands (`rm`, `del`, `Remove-Item`, `git rm`) on Vault notes are strictly forbidden (`[OBS-ASI03-02]`). Set `status: superseded` and `supersedes: [[note]]`. |
| **Core Rules HITL Gate** | Require explicit Human-in-the-Loop approval (`ask_question`) before creating or patching any note inside `00-core-rules/` (`[OBS-ASI06-01]`). |
| **Empirical DoD Evidence** | Patching a Living DoD checkbox from `- [ ]` to `- [x]` requires empirical evidence: commit hash, test output summary, or audit report link (`[OBS-ASI09-06]`). |
| **Metadata & Schema Gate** | Frontmatter: `type` (`adr`, `domain_rule`, `pivot`, `sdd`, `bdd`, `dod`, `audit`, `changelog`, `epic`), `feature`, `project: antigravity`, `date` (`YYYY-MM-DD`), `description`, `tags`. Verified via [`validate_vault_note.py`](./scripts/validate_vault_note.py) (`[OBS-LLM10-03]`). |
| **Parity** | Links must resolve to disk (`00-core-rules/`, `01-concepcao/`, etc.) (`[OBS-ASI08-05]`). |

---

## Execution Pipeline

| Step | Directive | Refs |
| :--- | :--- | :--- |
| **1. Index** | Run `search_query` with sanitized metadata keys (`[OBS-LLM09-04]`). Check `backlinks` on `00-core-rules/`. | [`obsidian-protocol.md`](./references/obsidian-protocol.md) |
| **2. Create / Patch** | Require `ask_question` approval before touching `00-core-rules/`. Create via [`note-template.md`](./resources/note-template.md) or patch via `vault_patch` (require commit/test/audit evidence for DoD `- [x]`). Never overwrite or delete notes. | [`note-template.md`](./resources/note-template.md), [`obsidian-protocol.md`](./references/obsidian-protocol.md) |
| **3. Validate** | Run `python skills/obsidian/scripts/validate_vault_note.py <note_path> [--vault-root <dir>]` after creating or patching any note. Enforce exit code `0` (valid schema, zero `[MEMORY_POISONING_RISK]`, zero broken wikilinks). | [`validate_vault_note.py`](./scripts/validate_vault_note.py), [`obsidian-protocol.md`](./references/obsidian-protocol.md) |
| **4. Link** | Maintain acyclic bidirectional wikilinks verified on disk. | [`obsidian-example.md`](./examples/obsidian-example.md) |
