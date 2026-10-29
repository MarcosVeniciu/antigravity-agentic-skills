# Behavioral Specification Guide: Pure BDD Gherkin (`plan-bdd`)

This guide defines the standards for formulating behavioral specifications during Phase 1 (`/plan`), ensuring that feature requirements are expressed in accessible business language without leaking technical implementation details.

---

## 1. Context-Zero Authoring via `bdd-architect`

To prevent the Socratic interview transcript from contaminating behavioral specifications with technical jargon or unspoken assumptions:
- Step 3 is executed by the isolated `bdd-architect` subagent (`Model: "inherit"`, `EnableWriteTools: true`) as defined in [`references/plan-goldfish.md`](./plan-goldfish.md).
- The subagent receives **only** the approved Desired End-State and Architectural Proposal summary, never the raw Step 1 chat history.

---

## 2. Golden Rules of BDD

1. **Ubiquitous, Accessible Language:**
   - Scenarios must be readable and verifiable by developers, product managers, and business stakeholders alike.
   - **Forbidden Technical Jargon:** Never use database or HTTP terminology in Gherkin steps:
     - ❌ Prohibited: `SELECT * FROM producers`, `HTTP 200 OK`, `POST /api/v1/checkout`, `JSON payload`, `foreign key`.
     - ✅ Allowed: *"the producer details are saved"*, *"the system confirms successful registration"*, *"the user submits registration data"*.
2. **Behavioral Intent Over UI Mechanics:**
   - Describe what the user intends to achieve rather than specific UI button clicks:
     - ❌ Weak: *"When user clicks the blue button with ID #submit-btn"*
     - ✅ Strong: *"When the user submits the registration request"*
3. **Fidelity to Approved Architectural Proposal:**
   - The scenarios must strictly match the Desired End-State selected during the scope debate ([`references/plan-debate.md`](./plan-debate.md)).

---

## 3. Mandatory Coverage Matrix

Every behavioral specification artifact (`01-concepcao/bdd-[slug].md`) **MUST** cover both positive and negative categories:

| Category | Tag | Focus | Examples |
|---|---|---|---|
| **Happy Path** | `@happy-path` | Ideal successful user journey with valid data and expected state transitions | Standard registration, successful checkout, valid state transition |
| **Unhappy Paths** | `@unhappy-path` | Recoverable errors, validation failures, boundary rejections | Missing required fields, duplicate identifier, invalid password format |
| **Security / Auth** | `@security` | Permission boundaries, access denials, role restrictions | Unauthenticated request, forbidden role access, expired session |
| **Concurrency / State** | `@concurrency` | Conflicting state, race conditions, double submissions | Concurrent duplicate registration, concurrent balance deduction |

> [!IMPORTANT]
> **Cross-Artifact Parity with SDD:** Every `@unhappy-path`, `@security`, and `@concurrency` scenario defined here will be verified against `01-concepcao/sdd-[slug].md` by both [`scripts/validate_sdd_contracts.py`](../scripts/validate_sdd_contracts.py) and the `goldfish-adversary` subagent.

---

## 4. Gherkin Structural Pattern

```gherkin
Feature: [Feature Name]
  In order to [Achieve Business Value / Prevent Risk]
  As a [Specific User Persona / Role]
  I want [Observable System Capability]

  @happy-path
  Scenario: [Clear description of success scenario]
    Given [Initial system state and prerequisites]
    When [User or external system action occurs]
    Then [Observable business outcome achieved]
    And [System state verification]

  @unhappy-path @validation
  Scenario: [Clear description of rejection or validation scenario]
    Given [Initial system state with existing record or condition]
    When [Invalid action or conflicting input is submitted]
    Then [System rejects the action with specific business explanation]
    And [No corrupt or partial state is persisted]
```

---

## 5. Artifact Storage & Integration

- Specifications are saved at `01-concepcao/bdd-[slug].md` in the Obsidian Vault or documentation directory using the format in [`resources/plan-template.md`](../resources/plan-template.md).
- BDD scenarios serve as the sole behavioral input for `sdd-architect` in Step 4 and for Phase 2 unit tests (`/implement`).
- See a complete working example in [`examples/plan-example.md`](../examples/plan-example.md).
