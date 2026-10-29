# Context-Zero Subagent Orchestration & Goldfish Council Guide (`plan-goldfish`)

This guide governs the **SDD 2.0 (Elephant & Goldfish)** multi-agent architecture during Phase 1 (`/plan`), eliminating context contamination, self-agreement bias, and unchallenged specification gaps.

---

## 1. The Context Firewall Principle

In SDD 1.0, a single agent conducts the Socratic debate (Step 1), writes the BDD specification (Step 3), designs the SDD contracts (Step 4), and approves its own checklist (Step 5). Because the agent retains the entire conversation history in its context window, it mentally fills in missing rules and overlooks ambiguities.

To enforce true **Context-Zero Isolation** within a single user chat session:
1. **The Main Agent acts strictly as the Orchestrator ("Maestro"):**
   - Conducts Step 1 (Outcome-Based Scope Debate via `ask_question`).
   - Executes Step 2 (Git Flow branch isolation via [`scripts/validate_branch.py`](../scripts/validate_branch.py)).
   - Presents generated artifacts and arbitration matrices to the user (`RequestFeedback: true` / `ask_question`).
   - Initializes the Living DoD and executes the Phase 1 squash commit (Step 6).
2. **Strict Context Sanitization:**
   - When invoking `bdd-architect` or `sdd-architect`, **NEVER** paste the raw Socratic chat transcript.
   - Pass **only** the approved Desired End-State summary, the selected Architectural Proposal tier, and the physical file paths on disk.

---

## 2. Authoring Subagents (Steps 3 & 4)

Use `define_subagent` and `invoke_subagent` with **`Model: "inherit"`** and **`EnableWriteTools: true`** for the two authoring subagents so they leverage the primary architectural reasoning model active in the user's session.

### 2.1. Step 3 Author: `bdd-architect`
- **Configuration:**
  - `Name`: `"bdd-architect"`
  - `EnableWriteTools`: `true`
  - `Model`: `"inherit"`
- **SystemPrompt:**
  > *"You are a Context-Zero BDD Specification Architect. You receive an approved Desired End-State and Architectural Proposal summary without prior chat bias. Formulate pure Gherkin behavioral specifications (`@happy-path`, `@unhappy-path`, `@security`, `@concurrency`) strictly following `skills/plan/references/plan-bdd.md`. Never leak technical jargon (SQL, HTTP status codes, JSON keys, class names) into Gherkin steps. Save the artifact to `01-concepcao/bdd-[slug].md`."*
- **Orchestrator Gate:** Once `bdd-architect` completes, the Orchestrator summarizes or links `01-concepcao/bdd-[slug].md` and verifies user approval before invoking `sdd-architect`.

### 2.2. Step 4 Author: `sdd-architect`
- **Configuration:**
  - `Name`: `"sdd-architect"`
  - `EnableWriteTools`: `true`
  - `Model`: `"inherit"`
- **SystemPrompt:**
  > *"You are a Context-Zero Software Design Description (SDD) Architect. You have ZERO access to the initial user debate. Read strictly `01-concepcao/bdd-[slug].md`, the repository manifests/structure, and `skills/plan/references/plan-sdd.md`. Translate every BDD scenario into Clean Architecture boundaries, a Mermaid `sequenceDiagram` (with `autonumber`, double-quoted message labels, and `alt/else` error branches for every negative BDD scenario), a Mermaid `classDiagram` (with `<<Interface>>` ports, `<<Fake>>` test doubles, and 100% method parity with the `sequenceDiagram`), typed contracts, and a File Impact Analysis table. Save to `01-concepcao/sdd-[slug].md` and run `python skills/plan/scripts/validate_sdd_contracts.py 01-concepcao/sdd-[slug].md --bdd 01-concepcao/bdd-[slug].md` until it passes with exit code 0."*

---

## 3. Step 5: The Parallel "Goldfish Council" Blind Review

Immediately after `sdd-architect` generates and validates `01-concepcao/sdd-[slug].md`, the Orchestrator defines and invokes **3 read-only subagents in parallel** (in the same tool-call turn) using **`Model: "flash"`** and **`EnableWriteTools: false`**.

> [!TIP]
> **Why `Model: "flash"` for the Goldfish Council?**
> Each Goldfish persona operates in strictly read-only mode over two already-written files (`bdd-[slug].md` and `sdd-[slug].md`) through a single, narrow analytical lens. Running `Model: "flash"` in parallel delivers near-instant execution and minimal quota consumption while maintaining high adversarial precision.

### 3.1. Persona 1: `goldfish-yagni` (Simplicity & Anti-Overengineering Critic)
- **Configuration:** `EnableWriteTools: false`, `Model: "flash"`, `Role: "YAGNI & Simplicity Critic"`
- **SystemPrompt:**
  > *"You are the YAGNI Goldfish Critic (Context-Zero, Read-Only). Inspect `01-concepcao/bdd-[slug].md`, `01-concepcao/sdd-[slug].md`, and the existing codebase structure. Attack accidental complexity: identify unnecessary layers, speculative abstractions, redundant DTOs/interfaces that duplicate existing repository modules, or violations of Clean Architecture boundaries. Return a concise bulleted list of findings classified as `[CRITICAL]`, `[MODERATE]`, or `[LOW]`, or state `ZERO_FINDINGS`."*

### 3.2. Persona 2: `goldfish-adversary` (Concurrency, Security & Edge-Case Hunter)
- **Configuration:** `EnableWriteTools: false`, `Model: "flash"`, `Role: "Adversarial & Concurrency Critic"`
- **SystemPrompt:**
  > *"You are the Adversarial Goldfish Critic (Context-Zero, Read-Only). Inspect `01-concepcao/bdd-[slug].md` and `01-concepcao/sdd-[slug].md`. Hunt for logical holes: race conditions (TOCTOU, double submission), partial/orphan state on failure, missing idempotency, unmapped `@unhappy-path`/`@security`/`@concurrency` scenarios from BDD that lack explicit `alt/else` branches or typed exceptions in SDD, and authorization bypasses. Return a concise bulleted list of findings classified as `[CRITICAL]`, `[MODERATE]`, or `[LOW]`, or state `ZERO_FINDINGS`."*

### 3.3. Persona 3: `goldfish-implementer` (Blind TDD Developer Simulator)
- **Configuration:** `EnableWriteTools: false`, `Model: "flash"`, `Role: "Blind TDD Implementer Critic"`
- **SystemPrompt:**
  > *"You are the Blind TDD Implementer Goldfish (Context-Zero, Read-Only). Simulate a developer opening a brand-new chat in Phase 2 (`/implement`) who only has access to `01-concepcao/bdd-[slug].md` and `01-concepcao/sdd-[slug].md`. Identify any ambiguity that would force you to guess during TDD Red/Green phases: missing parameter/return types, undefined validation constraints, discrepancies between `sequenceDiagram` and `classDiagram` method signatures, or underspecified `<<Fake>>` test double behavior. Return a concise bulleted list of findings classified as `[CRITICAL]`, `[MODERATE]`, or `[LOW]`, or state `ZERO_FINDINGS`."*

---

## 4. Interactive Arbitration Gate & Surgical Remediation

When all 3 Goldfish subagents return their reports to the Orchestrator:

1. **Consolidate into the Goldfish Arbitration Matrix:**
   Present a clean summary table in chat grouping deduplicated findings by persona:
   ```markdown
   | # | Persona | Severity | Finding / Ambiguity | Recommended Action |
   |---|---|---|---|---|
   | 1 | 🐠 `goldfish-adversary` | High | Concurrent duplicate request lacks unique constraint / lock handling in `Service` | Add `DuplicateConflictError` & `alt` branch in SDD |
   | 2 | 🐠 `goldfish-yagni` | Medium | `CustomMapperFactory` is redundant for single DTO | Inline mapping into DTO classmethod |
   | 3 | 🐠 `goldfish-implementer` | Low | `InMemoryRepo` fake missing `seed()` helper signature | Add `+seed(items: list) void` to `classDiagram` |
   ```
2. **Query User Verdict via `ask_question`:**
   Use the interactive `ask_question` tool (`is_multi_select: true` or structured options) so the user decides which findings to **Accept**, **Defer**, or **Reject**.
3. **Apply Surgical Revisions:**
   - For accepted SDD adjustments, message the existing `sdd-architect` (`send_message` with its `conversationId`) to apply surgical edits to `01-concepcao/sdd-[slug].md` and re-run [`scripts/validate_sdd_contracts.py`](../scripts/validate_sdd_contracts.py).
   - For accepted BDD adjustments, message `bdd-architect` to update `01-concepcao/bdd-[slug].md`.
4. **Proceed to Living DoD (Step 6):**
   Once the revised artifacts pass validation, record the Goldfish Council arbitration outcome in `01-concepcao/dod-[slug].md` ([`references/plan-dod.md`](./plan-dod.md)).
