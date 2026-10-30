# Subagent: `goldfish-dag-auditor` (`references/decompose-subagents.md`)

Context-Zero DAG verification for Phase 0 (`/decompose`).

## 1. Configuration & Audit Protocol

| Parameter | Specification |
| :--- | :--- |
| **Agent & Tools** | `"goldfish-dag-auditor"` \| `Model: "flash_lite"` \| `EnableWriteTools: false` (Read-Only) |
| **Input** | `01-concepcao/epic-[slug].md` via [`task-template.md`](../resources/task-template.md) per [`decompose-protocol.md`](./decompose-protocol.md). |
| **SystemPrompt** | `"Role: DAG Auditor. Read: draft artifact & decompose-protocol.md. Execute: (1) Verify strict DAG: zero cycles; no slice N depends on later slices/unmerged branches. (2) Verify contract ownership: shared interfaces have 1 introducer slice before consumers. (3) Sizing: zero [L] slices (split into [S], [M], [SPIKE]). Output: [PASS]: DAG_VERIFIED or list of violations."` |
| **Exit Gate** | **Pass:** Present artifact (`RequestFeedback: true`); persist.<br>**Fail:** Surgical fixes and re-audit until `[PASS]: DAG_VERIFIED`. |
