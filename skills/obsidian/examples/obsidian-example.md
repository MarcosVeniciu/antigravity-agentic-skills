# Example: Obsidian Vault Governance Walkthrough

This session demonstrates an agent using `/obsidian` to index vault knowledge, create an Architecture Decision Record (ADR), apply a surgical patch to a Living DoD, and link related documents via bidirectional wikilinks.

---

## Scenario: Adopting Redis Token Bucket Rate Limiting for API Endpoints

### Step 1: Pre-flight Vault Indexing & Discovery
The agent checks for existing rate-limiting decisions or ADRs in the vault:

```json
// Tool Call: search_query
{
  "query": "type: adr rate-limiting",
  "vaultPath": "00-core-rules/adrs"
}
```
*Result:* No existing ADR found for rate limiting. The agent checks `00-core-rules/conventions.md` to confirm existing infrastructure patterns.

---

### Step 2: Note Creation (ADR Generation)
The agent instantiates `00-core-rules/adrs/adr-0024-redis-rate-limiter.md` using the ADR template from [`../resources/note-template.md`](../resources/note-template.md):

```json
// Tool Call: vault_write
{
  "path": "00-core-rules/adrs/adr-0024-redis-rate-limiter.md",
  "content": "---\ntype: adr\nfeature: api-rate-limiter\nproject: antigravity\ndate: \"2026-10-26\"\ndescription: \"Adopts Redis-backed token bucket algorithm for API rate limiting\"\nstatus: accepted\ntags:\n  - adr\n  - architecture\n  - phase/concepcao\n---\n\n# ADR-0024: Redis Token Bucket Rate Limiter\n\n## Context & Problem Statement\nHigh-frequency public endpoints require distributed rate limiting to protect downstream services from burst traffic.\n\n## Decision Outcome\nAdopt Redis Lua-scripted token bucket algorithm over in-memory token bucket to support multi-instance cluster deployment.\n\n### Consequences\n* Positive: Atomic token consumption across multiple replicas.\n* Trade-off: Requires persistent Redis connectivity.\n\n## Links & Traceability\n* Justifies Contract: [[sdd-api-rate-limiter]]\n* Living DoD Reference: [[dod-api-rate-limiter]]\n"
}
```

---

### Step 3: Surgical Patching of Living DoD (`vault_patch`)
Rather than overwriting the entire `01-concepcao/dod-api-rate-limiter.md`, the agent applies a surgical heading patch to check off the ADR gate:

```json
// Tool Call: vault_patch
{
  "path": "01-concepcao/dod-api-rate-limiter.md",
  "targetType": "heading",
  "heading": "## Phase 1: Architectural Conception & SDD",
  "action": "replace",
  "content": "- [x] ADR-0024 documented and accepted: [[adr-0024-redis-rate-limiter]]\n- [x] SDD typed contract validated: [[sdd-api-rate-limiter]]\n- [ ] Living DoD initialized with all phase checkboxes"
}
```

---

### Step 4: Bidirectional Wikilink & Graph Validation
The agent verifies that both ends of the relationship resolve without dead links:
1. `[[adr-0024-redis-rate-limiter]]` in `dod-api-rate-limiter.md` resolves to `00-core-rules/adrs/adr-0024-redis-rate-limiter.md`.
2. `[[dod-api-rate-limiter]]` in `adr-0024-redis-rate-limiter.md` resolves to `01-concepcao/dod-api-rate-limiter.md`.
3. Backlinks query confirms bidirectional linkage.

*Result:* Knowledge graph remains cohesive, atomic, and free of orphan notes.
