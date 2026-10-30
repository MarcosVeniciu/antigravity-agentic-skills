# Behavioral Specification: Pure BDD Gherkin (`references/plan-bdd.md`)

Context-Zero BDD authoring via `bdd-architect` ([`plan-goldfish.md`](./plan-goldfish.md)).

## 1. Authoring Invariants & Scenario Matrix

| Invariant / Tag | Directives | Parity Target |
| :--- | :--- | :--- |
| **Context-Zero** | Receive only End-State + Proposal from [`plan-debate.md`](./plan-debate.md). Zero raw chat. | Eliminates bias leakage. |
| **Domain Terms** | ❌ No HTTP/SQL/JSON/classes.<br>✅ *"submits registration"*, *"confirms identity"*, *"details saved"*. | Stakeholder verifiable. |
| **`@happy-path`** | Primary valid journey. | Maps to SDD flow & return DTO. |
| **`@unhappy-path`** | Validation errors, missing fields, duplicate IDs. | Mandatory `alt/else` & `*Error` in SDD. |
| **`@security`** | Forbidden roles, expired tokens. | Security guard & exception in SDD. |
| **`@concurrency`** | Double-submit, race conditions. | Idempotency check in SDD. |

## 2. Gherkin Template

```gherkin
Feature: [Feature]
  In order to [Value] As a [Role] I want [Capability]

  @happy-path
  Scenario: [Success]
    Given [Prerequisites]
    When [Action]
    Then [Outcome] And [Verification]

  @unhappy-path @validation
  Scenario: [Rejection]
    Given [Existing record]
    When [Invalid input]
    Then [System rejects with explanation and zero corruption]
```

Save: `01-concepcao/bdd-[slug].md` via [`plan-template.md`](../resources/plan-template.md). Validate: [`validate_sdd_contracts.py`](../scripts/validate_sdd_contracts.py). Ref: [`plan-example.md`](../examples/plan-example.md).
