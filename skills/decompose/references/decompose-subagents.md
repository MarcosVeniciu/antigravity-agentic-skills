# Operational Guide: Context-Zero DAG & Slicing Auditor (`references/decompose-subagents.md`)

This guide governs the **SDD 2.0 (Elephant & Goldfish)** blind verification step during Phase 0 (`/decompose`), invoking a fast, read-only **`goldfish-dag-auditor`** subagent (`Model: "flash_lite"`) in Step 3 to verify that the decomposed epic (`01-concepcao/epic-[slug].md` or `task_list.md`) forms a valid Directed Acyclic Graph (DAG) with zero circular dependencies, zero oversized `L` slices, and explicit contract introducers.

---

## 1. Why Use a Blind `flash_lite` Subagent in `/decompose`?

During Step 1 and Step 2 of `/decompose`, the Main Orchestrator conducts the Socratic interview with the user and authors the evolutionary vertical slices. Because the Orchestrator holds the full debate in its context window, it can inadvertently overlook:
- A subtle circular dependency between Slice $A$ and Slice $B$.
- A shared boundary interface (`IRepository`, `IEventBus`) consumed by a slice without being explicitly introduced in an earlier batch/slice.
- A slice still sized as `L` (Large) that was not broken down into `S` or `M` single-chat sub-features.

Delegating the Step 3 pre-flight audit to **`goldfish-dag-auditor` (`Model: "flash_lite"`, `EnableWriteTools: false`)** provides an instant, near-zero-cost Context-Zero sanity check before asking the user for approval (`RequestFeedback: true`).

---

## 2. Step 3 Subagent: `goldfish-dag-auditor` (`Model: "flash_lite"`)

Define and invoke `goldfish-dag-auditor` during Step 3 (`EnableWriteTools: false`, `Model: "flash_lite"`):

- **Configuration:**
  - `Name`: `"goldfish-dag-auditor"`
  - `EnableWriteTools`: `false`
  - `Model`: `"flash_lite"`
  - `Role`: `"Context-Zero DAG & Evolutionary Slicing Auditor"`
- **Inputs Provided by Orchestrator:**
  - Draft decomposition artifact (`01-concepcao/epic-[slug].md` or `task_list.md`).
- **SystemPrompt:**
  > *"You are the Context-Zero DAG & Slicing Auditor (`goldfish-dag-auditor`, Read-Only, `Model: flash_lite`). Inspect the draft decomposition artifact (`01-concepcao/epic-[slug].md` or `task_list.md`) against `skills/decompose/references/decompose-protocol.md`. Verify strictly: (1) Acyclic Dependency Graph (DAG) — confirm zero circular dependencies and that no slice N depends on a later slice N+k or an unmerged parallel branch; (2) Contract Ownership — confirm every shared boundary interface/contract has a single explicit introducing slice prior to its consumers; (3) Single-Chat Sizing — confirm zero actionable slices remain sized as `L` (all `L` items must be decomposed into `S`, `M`, or timeboxed `Spike` tasks). Return `[PASS]: DAG_VERIFIED` or a concise list of violations for the Orchestrator to fix before presenting to the user."*
