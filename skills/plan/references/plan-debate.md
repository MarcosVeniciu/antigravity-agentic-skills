# Outcome-Based Scope Debate Specification (`references/plan-debate.md`)

Governs Phase 1 (`/plan` Step 1) scope debate, eliminating XY Problem and structuring proposals.

## 1. Alignment Invariants & Interview Protocol

| Dimension | Technical Directive & Invariants |
| :--- | :--- |
| **End-State** | Observable rules and state changes. Measurable criteria (latency, compatibility, schema). |
| **Intent Hints** | User suggestions are intent indicators, not constraints. Substitute resilient patterns. |
| **XY Problem** | Identify true goal **X** (e.g. prevent duplicates); discard fragile vehicle **Y** (e.g. shell regex). |
| **`ask_question`** | 3-5 questions/turn. Frame 2-4 choices; prefix recommended with `(Recommended)`. Terminate once boundaries clear. |

## 2. Architectural Proposal Matrix

Populate 2-3 distinct proposals in [`plan-template.md`](../resources/plan-template.md) (strict cap: 3):

| Proposal Tier | Architecture Strategy | Trade-offs & Fit |
| :--- | :--- | :--- |
| **Proposal 1: Pragmatic** | Incremental modification; leverages existing codebase. | Lowest effort; acceptable debt. |
| **Proposal 2: Scalable** | Decoupled Clean Architecture; abstract Ports; Fakes (`<<Fake>>`). | Maximum testability; higher initial abstraction. |
| **Proposal 3: Hybrid** | Balanced compromise between minimal code changes and modern patterns. | Optional middle-ground vector. |
