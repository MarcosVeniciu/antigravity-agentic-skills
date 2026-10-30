# Epic Debate & Socratic Alignment (`references/decompose-debate.md`)

Governs Phase 0 (`/decompose`) macro alignment, XY Problem elimination, and slicing strategy selection.

## 1. Alignment Invariants

| Invariant | Technical Directive |
| :--- | :--- |
| **End-State ($S_1 \dots S_n$)** | Invariant success signals: SLAs, throughput, latency, schema integrity. Paths negotiable. |
| **Hypotheses** | Tools, brokers, or services are hypotheses, never mandates. Eliminate premature optimization. |
| **XY Problem** | Identify root problem **X**; eliminate accidental infrastructure **Y** (e.g. broker vs outbox). |
| **Spikes** | Isolate unknown APIs or risks into timeboxed Spikes ($S \le 2\text{h}$) for ADR/PoC. |

## 2. Interview & Slicing Strategy Matrix

| Dimension | Specification |
| :--- | :--- |
| **Protocol (`ask_question`)** | 3-5 questions/turn on boundaries, SLAs, data retention, PII. Recommended option prefixed `(Recommended)`. |
| **1. MVP-First** | Minimal walking skeleton with observable end-to-end behavior; downstream slices harden/scale. |
| **2. Contract-First** | Domain models + boundary interfaces (`IRepository`, `IClient`) with Fakes; downstream slices add adapters. |
| **3. Strangler Fig** | Intercept legacy paths via proxies; route new workflows to modern components until cutover. Max 3 proposals. |
| **Exit Gate** | On approval, populate [`task-template.md`](../resources/task-template.md) and execute [`decompose-protocol.md`](./decompose-protocol.md). |
