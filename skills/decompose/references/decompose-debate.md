# Outcome-Based Epic Debate Guide (`decompose-debate`)

This guide governs the macro-architectural alignment interview in Phase 0 (`/decompose`), eliminating the XY Problem at the initiative level and structuring comparative slicing strategy proposals.

---

## 1. Core Directives: Macro Outcome-Based Alignment

1. **Focus on the Desired Observable End-State ($S_1 \dots S_n$):**
   - Identify: *"What is the observable business capability and system state when this entire epic is complete?"*
   - Define concrete, measurable acceptance signals ($S_1 \dots S_n$), such as transaction volume, latency boundaries, backward compatibility, and compliance gates.
   - The business destination is fixed; the technical roadmap and slicing sequence are negotiable.

2. **Treat User Implementation Suggestions as Hypotheses:**
   - When the user suggests specific tools, databases, distributed components, or architectures ("we need Kafka, microservices, and Redis"), treat them as clues of underlying requirements, **never as immutable mandates**.
   - If a proposed approach introduces accidental complexity or premature optimization, acknowledge the underlying need and propose simpler, evolutionary alternatives.

3. **Eliminating the Macro "XY Problem":**
   - *The Trap:* The user asks to build complex distributed infrastructure **Y** (e.g., an asynchronous message broker with custom retry queues) to solve problem **X** (e.g., reliable notification delivery without blocking web requests).
   - *The Solution:* Pinpoint **X**, discard fragile or overengineered **Y**, and offer evolutionary vertical slices starting from the simplest viable architectural mechanism.

4. **Spike Identification & Uncertainty Isolation:**
   - If a core architectural path depends on an unproven library, third-party API limit, or unknown performance characteristic, do not guess or block the epic.
   - Isolate a timeboxed **Spike** task ($S \le 2\text{h}$) to establish an ADR or proof-of-concept before proceeding with dependent slices.

---

## 2. Socratic Interview Protocol

1. **Adaptive Volume in Small Batches:**
   - Avoid overwhelming questionnaires or walls of text.
   - Ask **3 to 5 surgical, high-impact questions** per turn.
   - Focus strictly on:
     - Boundary constraints (SLAs, throughput, data retention).
     - Security and compliance (PII, authentication, auditability).
     - Integration points with legacy codebases and existing databases.
     - Phased delivery priorities (what must ship in MVP vs. subsequent milestones).

2. **Primary Channel: The `ask_question` Tool:**
   - Always prefer the interactive `ask_question` tool whenever choices, scope boundaries, trade-offs, or delivery phases can be structured.
   - Place the recommended architectural choice first, prefixed with `(Recommended)`.
   - Provide 2 to 4 concrete options framed from the user's perspective.

3. **Secondary Channel: Chat Fallback Template:**
   - When questions are exploratory or open-ended, format them using the structured block:
     ```markdown
     * **Scope Impact:** [Why this question influences epic slicing or dependency ordering]
     * **Question:** [Direct, high-impact question]
     * **Recommended Hypothesis:** [Default architectural assumption if user has no preference]
     ```

4. **Active Convergence:**
   - Conclude interviewing as soon as the desired end-state, domain boundaries, and delivery milestones are sufficiently clear to populate the Slicing Strategy Matrix.

---

## 3. Slicing Strategy Proposal Matrix

Consolidate understanding into 2 (default) or at most 3 distinct macro-slicing strategies:

- **Proposal 1 (Vertical Thin-Slice / MVP-First):**
  - Minimal initial scope delivering an end-to-end walking skeleton with basic observable behavior; subsequent slices incrementally enrich features, error handling, and scale.
- **Proposal 2 (Contract-First & Foundation-First):**
  - Establishes core domain entities, value objects, and boundary interfaces (`IRepository`, `IClient`) with in-memory Fakes first; subsequent slices attach concrete adapters and consumers monotonically.
- **Proposal 3 (Strangler Fig / Evolutionary Migration - Optional):**
  - Intercepts legacy calls via proxy adapters, routing new workflows to modern components while keeping existing operations intact until full cutover.

### Strict Cap:
Never present more than 3 proposals to prevent cognitive overload and decision paralysis.

---

## 4. Exit Criteria & Transition

- The debate phase terminates once the user approves or selects a macro-slicing strategy.
- Advance immediately to Step 2 (Evolutionary Slicing & Complexity Sizing) in [`references/decompose-protocol.md`](./decompose-protocol.md) and populate [`resources/task-template.md`](../resources/task-template.md).
