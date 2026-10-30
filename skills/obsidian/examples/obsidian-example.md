# Example: Obsidian Vault Governance Walkthrough

Execution trace for ADR creation via [`note-template.md`](../resources/note-template.md) and surgical DoD patching per [`obsidian-protocol.md`](../references/obsidian-protocol.md).

## 1. Execution Trace

| Step | Op | Tool Call & Payload | Target & Invariants |
| :--- | :--- | :--- | :--- |
| **1. Index** | Search | `search_query({"query": "type: adr rate-limiting"})` | Check `00-core-rules/conventions.md`. |
| **2. Create** | Write | `vault_write({"path": "00-core-rules/adrs/adr-0024-redis-rate-limiter.md", ...})` | Instantiate from [`note-template.md`](../resources/note-template.md). |
| **3. Patch** | Patch | `vault_patch({"path": "01-concepcao/dod-api-rate-limiter.md", "targetType": "heading", "heading": "## Phase 1", ...})` | Surgical DoD update; zero overwrites. |
| **4. Verify** | Audit | `backlinks({"note": "adr-0024-redis-rate-limiter"})` | Bidirectional parity with DoD. |
