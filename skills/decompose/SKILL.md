---
name: decompose
description: Decomposes complex architectural initiatives and multi-stage epics into atomic, evolutionary vertical slices and task checklists verified by a Context-Zero DAG auditor (flash_lite).
---

# Task Decomposition & Epic Slicing (`/decompose`)

Decomposes epics into vertical slices and checklists verified by Context-Zero `goldfish-dag-auditor` (`Model: "flash_lite"`). Output: `01-concepcao/epic-[slug].md` via [`task-template.md`](./resources/task-template.md).

## Execution Pipeline

| Step / Gate | Actor | Technical Directive & Invariants | CLI / Refs |
| :--- | :--- | :--- | :--- |
| **1. Alignment** | `Orchestrator` | Ingest requirements/ADRs. Define End-State ($S_1 \dots S_n$). Eliminate XY Problem via 3-5 questions/turn. Formulate Strategy Matrix (MVP-First, Contract-First, Strangler Fig; max 3). Isolate Spikes ($S \le 2\text{h}$). | `ask_question`<br>[`decompose-debate.md`](./references/decompose-debate.md) |
| **2. Slicing** | `Orchestrator` | Apply 5 Principles (Verifiable, Compatible, Explicit Boundaries, Incremental Integration, Single-Chat). Enforce Sizing: `[S]` (1-2 files), `[M]` (3-5 files), `[SPIKE]` ($\le 2\text{h}$); `[L]` **prohibited**. Sequence: Core $\rightarrow$ Domain/Fakes $\rightarrow$ Adapters/DI. Conditionals: 1 line or `N/A`. | [`decompose-protocol.md`](./references/decompose-protocol.md)<br>[`task-template.md`](./resources/task-template.md) |
| **3.1 DAG Audit** | `goldfish-dag-auditor`<br>(`flash_lite`, read-only) | Context-Zero check: strict DAG (zero cycles, no unmerged parallel deps); contract introducers precede consumers; zero `[L]` slices. Returns `[PASS]: DAG_VERIFIED`. | [`decompose-subagents.md`](./references/decompose-subagents.md) |
| **3.2 Approval** | `Orchestrator` | Present decomposition artifact (`RequestFeedback: true`). Persist blueprint to `01-concepcao/epic-[slug].md`. | [`decompose-example.md`](./examples/decompose-example.md)<br>[`task-template.md`](./resources/task-template.md) |
