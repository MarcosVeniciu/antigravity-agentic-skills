# Outcome-Based Scope Debate Guide (`plan-debate`)

This guide governs the technical alignment interview in Phase 1 (`/plan`), eliminating the XY Problem and structuring comparative architectural proposals.

---

## 1. Core Directives: Outcome-Based Prompting

1. **Focus on the Desired End-State (Fixed):**
   - Identify: *"What is the real, observable business rule and functional outcome the user needs to achieve?"*
   - Define measurable acceptance signals (e.g., latency boundaries, backward compatibility, schema invariance).
   - The destination is fixed; the implementation path is negotiable.
2. **User Implementation Hints Are Hypotheses (Flexible):**
   - When the user proposes specific libraries, scripts, or files ("how to do it"), treat them as clues of underlying intent, **never as immutable mandates**.
   - If a proposed technique is fragile or anti-pattern, acknowledge their intent, discard the flawed approach, and propose robust architectural alternatives.
3. **Eliminating the "XY Problem":**
   - *The Trap:* The user wants to achieve **X** (e.g., prevent duplicate email registrations), but asks how to do **Y** (e.g., write a custom regex parser in a shell script).
   - *The Solution:* Identify **X**, discard fragile **Y**, and offer standard patterns (e.g., unique database constraint with repository validation).

---

## 2. Socratic Interview Protocol

1. **Adaptive Volume in Small Batches:**
   - Never send overwhelming walls of text or long questionnaires.
   - Ask **3 to 5 surgical, objective questions** per interaction turn.
2. **Primary Channel: The `ask_question` Tool:**
   - Always prefer the interactive `ask_question` tool whenever choices, scope limits, trade-offs, or error paths can be structured.
   - Place the recommended choice first, prefixed with `(Recommended)`.
   - Provide 2 to 4 concrete options framed from the user's perspective.
3. **Secondary Channel: Chat Fallback Template:**
   - For exploratory or subjective inquiries, format questions in chat using the 3-part block:
     ```markdown
     * **Scope Impact:** [Why this question matters to business rules or failure modes]
     * **Question:** [Direct, surgical question]
     * **Recommended Hypothesis:** [Default technical assumption if user has no preference]
     ```
4. **Active Convergence:**
   - Conclude interviewing as soon as the functional outcome, boundary rules, and success criteria are sufficient to populate the proposal matrix.

---

## 3. Architectural Proposal Matrix

Consolidate understanding into 2 (default) or at most 3 distinct proposals:

- **Proposal 1 (Pragmatic / Incremental):**
  - Minimal friction with existing code, lowest implementation cost, keeps viable user suggestions.
- **Proposal 2 (Architecturally Ideal / Scalable):**
  - Decoupled Clean Architecture, modern best practices, high testability with in-memory test doubles.
- **Proposal 3 (Balanced / Hybrid - Optional):**
  - Practical middle-ground balancing moderate refactoring with modern patterns, or alternative tech vector.

### Strict Cap:
Never present more than 3 proposals to prevent cognitive overload and decision paralysis.

---

## 4. Exit Criteria & Transition

- The debate phase terminates immediately once the user approves or selects a proposal.
- Advance directly to Step 2 (Branch Strategy) and Step 3 (BDD Modeling) using [`resources/plan-template.md`](../resources/plan-template.md).
