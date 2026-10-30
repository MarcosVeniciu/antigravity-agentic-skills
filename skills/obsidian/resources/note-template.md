# Unpopulated Templates for Obsidian Vault Notes

This resource provides standard, unpopulated templates for Architecture Decision Records (ADRs), Business Domain Rules, and Technical Pivot Notes. Copy and populate the appropriate section when creating notes.

---

## Template 1: Architecture Decision Record (ADR)

```markdown
---
type: adr
feature: "{{FEATURE_SLUG}}"
project: antigravity
date: "{{DATE}}"
description: "{{DESCRIPTION}}"
status: proposed
tags:
  - adr
  - architecture
  - phase/concepcao
---

# ADR-{{ADR_NUMBER}}: {{TITLE}}

## Context & Problem Statement
Describe the technical context, business driver, and problem prompting this architectural decision.

## Decision Drivers
* Driver 1: Performance, throughput, or latency constraints
* Driver 2: Security, compliance, or regulatory requirements
* Driver 3: Team maintainability, simplicity, or time to market

## Considered Options
1. **Option A:** {{OPTION_A_TITLE}} — Brief description
2. **Option B:** {{OPTION_B_TITLE}} — Brief description

## Decision Outcome
Chosen option: **{{CHOSEN_OPTION}}**, because {{REASONING}}.

### Positive Consequences
* Benefit 1: {{BENEFIT_1}}
* Benefit 2: {{BENEFIT_2}}

### Negative Consequences / Trade-offs
* Trade-off 1: {{TRADE_OFF_1}}
* Trade-off 2: {{TRADE_OFF_2}}

## Security & Threat Considerations
* Authentication / Authorization Impact: {{AUTH_IMPACT}}
* Data Sensitivity & Secret Containment: {{SECRET_CONTAINMENT}}
* OWASP LLM / Agentic Risk Mitigation: {{OWASP_MITIGATION}}

## Links & Traceability
* Supersedes: [[{{SUPERSEDED_ADR}}]] (or None)
* Justifies Contract: [[sdd-{{FEATURE_SLUG}}]]
* Living DoD Reference: [[dod-{{FEATURE_SLUG}}]]
```

---

## Template 2: Business Domain Rule

```markdown
---
type: domain_rule
feature: global
project: antigravity
date: "{{DATE}}"
description: "{{DESCRIPTION}}"
status: active
tags:
  - domain
  - business-rule
  - core
---

# Business Rule: {{RULE_IDENTIFIER}} - {{TITLE}}

## Ubiquitous Definition
State the business domain rule in precise, unambiguous domain terms agreed upon with domain stakeholders.

## Invariants & Acceptance Constraints
* **Invariant 1:** {{INVARIANT_CONDITION_1}}
* **Invariant 2:** {{INVARIANT_CONDITION_2}}
* **Constraint 3:** {{BOUNDARY_LIMIT_3}}

## Security Invariants & Access Controls
* **Required Role / Permission:** {{REQUIRED_PERMISSION}}
* **Input Validation & Sanitization:** {{VALIDATION_BOUNDARY}}
* **Audit & Non-Repudiation Requirement:** {{AUDIT_TRAIL_RULE}}

## Calculations / State Transitions
Describe exact mathematical formulas, state machine transitions, or validation logic:
```
State: DRAFT -> (Event: Submit) -> PENDING_APPROVAL -> (Event: Approve) -> ACTIVE
```

## System Impacts & Enforcing Components
* Domain Entity: `src/domain/{{ENTITY_NAME}}`
* Specification: [[sdd-{{FEATURE_SLUG}}]]
* Validation Service: `src/services/{{VALIDATOR_SERVICE}}`
```

---

## Template 3: Technical Pivot Note

```markdown
---
type: pivot
feature: "{{FEATURE_SLUG}}"
project: antigravity
date: "{{DATE}}"
description: "{{DESCRIPTION}}"
status: completed
tags:
  - pivot
  - bugfix
  - phase/auditorias
---

# Pivot: {{PIVOT_TITLE}}

## Bug Context & Technical Deviation
Detail the failure, unexpected API behavior, runtime bottleneck, or contract mismatch discovered during implementation.
* Observed Behavior: {{OBSERVED_BEHAVIOR}}
* Expected Contract: {{EXPECTED_CONTRACT}}

## Root Cause Analysis
Explain the fundamental reason for the deviation (e.g. library limitation, concurrency race, undocumented third-party payload).

## Adopted Solution & Architecture Pivot
Describe the pivot decision, alternative pattern, or refactoring implemented to overcome the obstacle.
* Previous Design: {{OLD_DESIGN}}
* New Design: {{NEW_DESIGN}}

## Lessons Learned & Prevention Invariants
Specify guidelines, regression test patterns, or static rules to ensure this pitfall is avoided in future features.

## Relationships & Traceability
* Related SDD Contract: [[sdd-{{FEATURE_SLUG}}]]
* Originating Test Suite: `tests/unit/test_{{COMPONENT}}.py`
* Living DoD Checkpoint: [[dod-{{FEATURE_SLUG}}]]
```
