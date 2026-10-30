---
type: plan
feature: "{{FEATURE_SLUG}}"
project: antigravity
date: "{{DATE}}"
description: "{{DESCRIPTION}}"
tags:
  - plan
  - conception
  - bdd
  - sdd
  - dod
---

# Architectural Conception & Specification Plan: {{FEATURE_NAME}}

---

## 1. Technical Goal & Desired End-State
- **Functional Outcome:** {{FUNCTIONAL_OUTCOME}}
- **Business Value:** {{BUSINESS_VALUE}}
- **Measurable Success Criteria:** {{SUCCESS_CRITERIA}}

---

## 2. Scope Debate & Architectural Proposals

### Proposal 1: Pragmatic / Incremental
* **Approach:** {{P1_APPROACH}}
* **Advantages:** {{P1_PROS}}
* **Trade-offs:** {{P1_CONS}}
* **Estimated Impact:** {{P1_IMPACT}}

### Proposal 2: Architecturally Ideal / Scalable (Recommended)
* **Approach:** {{P2_APPROACH}}
* **Advantages:** {{P2_PROS}}
* **Trade-offs:** {{P2_CONS}}
* **Estimated Impact:** {{P2_IMPACT}}

### Selected Decision:
> **Approved Proposal:** {{SELECTED_PROPOSAL}}  
> **Rationale:** {{SELECTION_RATIONALE}}

---

## 3. Sequential Implementation Plan

| # | Action | Rationale | Technical Acceptance Criteria | Dependency |
|---|---|---|---|---|
| 1 | {{STEP_1_ACTION}} | {{STEP_1_RATIONALE}} | {{STEP_1_CRITERIA}} | — |
| 2 | {{STEP_2_ACTION}} | {{STEP_2_RATIONALE}} | {{STEP_2_CRITERIA}} | Step 1 |
| 3 | {{STEP_3_ACTION}} | {{STEP_3_RATIONALE}} | {{STEP_3_CRITERIA}} | Step 2 |

---

## 4. Behavioral Specification (BDD)

```gherkin
Feature: {{FEATURE_NAME}}
  In order to {{BUSINESS_VALUE}}
  As a {{USER_ROLE}}
  I want {{FUNCTIONAL_DESIRE}}

  @happy-path
  Scenario: Successful Happy Path Execution
    Given {{HAPPY_GIVEN}}
    When {{HAPPY_WHEN}}
    Then {{HAPPY_THEN}}
    And {{HAPPY_AND}}

  @unhappy-path @validation
  Scenario: Rejection of Invalid or Conflicting Request
    Given {{UNHAPPY_GIVEN}}
    When {{UNHAPPY_WHEN}}
    Then {{UNHAPPY_THEN}}

  @security
  Scenario: Rejection of Unauthorized Caller
    Given {{SECURITY_GIVEN}}
    When {{SECURITY_WHEN}}
    Then {{SECURITY_THEN}}
```

---

## 5. Architecture & Contracts (SDD)

### Technical Execution Flow (Sequence Diagram) [Mandatory]

```mermaid
sequenceDiagram
    autonumber
    participant Client as "Client / Caller"
    participant API as "Controller / Endpoint"
    participant Service as "Domain Service"
    participant Port as "Repository / Port"
    
    Client->>API: "POST /resource (RequestDTO)"
    alt Unauthorized Role (@security)
        API-->>Client: "HTTP 403 Forbidden (ForbiddenError)"
    else Authorized Caller
        API->>Service: "execute(req)"
        Service->>Port: "find_by_id(id)"
        alt Entity Already Exists (@unhappy-path)
            Port-->>Service: "existing_entity"
            Service-->>API: "DuplicateEntityError"
            API-->>Client: "HTTP 409 Conflict"
        else Entity Available (@happy-path)
            Port-->>Service: "None (Available)"
            Service->>Port: "save(entity)"
            Port-->>Service: "persisted_entity"
            Service-->>API: "ResponseDTO"
            API-->>Client: "HTTP 201 Created (ResponseDTO)"
        end
    end
```

### Component & Contract Structure (Class Diagram) [Mandatory]

```mermaid
classDiagram
    direction TB

    class FeatureController {
        +handle_request(req: RequestDTO) ResponseDTO
    }

    class FeatureService {
        -port: IFeaturePort
        +execute(req: RequestDTO) ResponseDTO
    }

    class IFeaturePort {
        <<Interface>>
        +save(entity: Entity) Entity
        +find_by_id(id: str) Entity
    }

    class InMemoryFeaturePort {
        <<Fake>>
        -_storage: dict
        +save(entity: Entity) Entity
        +find_by_id(id: str) Entity
    }

    FeatureController --> FeatureService : invokes
    FeatureService --> IFeaturePort : depends on
    InMemoryFeaturePort ..|> IFeaturePort : implements
```

### Typed Contracts, Security Metadata & Boundary Mocks [Mandatory]

```yaml
security:
  authorization_scope: "{{REQUIRED_RBAC_ROLE_OR_SCOPE}}"
  rate_limit_tier: "strict"
  idempotency_required: true
  sensitive_fields:
    - "identifier"
```

```python
# Language-native typed contracts (e.g., Pydantic)
from pydantic import BaseModel, Field

class ForbiddenError(Exception):
    """Raised when caller lacks the required authorization_scope (HTTP 403)."""

class DuplicateEntityError(Exception):
    """Raised when an entity with the given identifier already exists (HTTP 409)."""

class RequestDTO(BaseModel):
    name: str = Field(..., min_length=2, description="Entity name")
    identifier: str = Field(..., description="Unique business identifier (redact in logs)")

class ResponseDTO(BaseModel):
    id: str = Field(..., description="Generated UUID")
    status: str = Field(default="active", description="Status code")
```

---

## 6. Requirements Traceability & Goldfish Council Arbitration

> **Traceability Standard:** Aligned with IEEE 829 and ISO/IEC/IEEE 29119 (Requirements Traceability Matrix).

| BDD Scenario / User Requirement | SDD Contract / Component | Impacted Source Files | Living DoD Acceptance Gate | Traceability Status |
| :--- | :--- | :--- | :--- | :---: |
| `@happy-path` (Scenario 1) | `FeatureController.handle_request` | `src/api/routes.py` | 100% Green Unit Tests | 🟢 **Mapped** |
| `@unhappy-path` (Scenario 2) | `DuplicateEntityError` / `RequestDTO` | `src/domain/entities.py` | HTTP 409 / 422 Rejection Test | 🟢 **Mapped** |
| `@security` (Scenario 3) | `ForbiddenError` / `security.authorization_scope` | `src/api/routes.py` | HTTP 401 / 403 Auth Guard Test | 🟢 **Mapped** |
| Boundary Integration | `IFeaturePort.save` / Adapter | `src/infra/repo.py` | Contract Test with Fake/Mock | 🟡 **Attention** ([see Architectural Point 1](#-architectural-point-1)) |

### Goldfish Council Blind Review Summary (Step 5 — Structured JSON Schema)

| Persona (`Model: "flash"`) | Severity & Category | Finding / Critique | User Arbitration Decision | Patch Applied |
| :--- | :---: | :--- | :---: | :--- |
| 🐠 `goldfish-yagni` | {{YAGNI_SEVERITY}} | {{YAGNI_FINDING}} | {{YAGNI_DECISION}} | {{YAGNI_PATCH}} |
| 🐠 `goldfish-adversary` | {{ADVERSARY_SEVERITY}} | {{ADVERSARY_FINDING}} | {{ADVERSARY_DECISION}} | {{ADVERSARY_PATCH}} |
| 🐠 `goldfish-implementer` | {{IMPLEMENTER_SEVERITY}} | {{IMPLEMENTER_FINDING}} | {{IMPLEMENTER_DECISION}} | {{IMPLEMENTER_PATCH}} |

### Architectural Points of Attention & Trade-Offs

#### 📌 Architectural Point 1: [Critical Integration / Trade-off Description]
* **Target Interface / Component:** `[path/to/component.py]`
* **Identified Risk / Tension:** [e.g., Latency impact, external dependency availability, strict boundary isolation]
* **Mitigation Strategy:** [e.g., Asynchronous worker, fallback cache, interface inversion via Port]
* **Verification Criteria:** [How the automated test suite will prove this point is resolved]

---

## 7. File Impact Analysis

| File / Module | Change Type | Risk Level | Description & Rationale |
|---|---|---|---|
| `src/domain/entities.py` | Additive (New) | Low | Domain entity definition |
| `src/domain/ports.py` | Additive (New) | Low | Interface port abstractions |
| `src/services/feature_service.py` | Additive (New) | Medium | Core business logic |
| `src/api/routes.py` | Mutative (Edit) | Medium | Add controller route mapping |

---

## 8. Living Definition of Done (DoD) Setup

- [x] Phase 1: Architectural Conception & Planning completed (SDD 2.0 + Goldfish Council)
- [ ] Phase 2: Iterative TDD Implementation (`/implement`)
- [ ] Phase 3: Macro-Refactoring across diff (`/refactor`)
- [ ] Phase 4: Specialized 5-Domain Audits (`/review`)
- [ ] Phase 5: Documentation & Feature Freeze (`/docs`)
