# Software Design Description Guide: Architecture & Contracts (`plan-sdd`)

This guide establishes the architectural standards for creating the Software Design Description (SDD) during Phase 1 (`/plan`), ensuring robust technical modeling before entering the TDD implementation cycle.

---

## 1. Clean Architecture & Dependency Inversion Principle (DIP)

Every technical design must adhere strictly to Clean Architecture boundaries:

```
[ Outer Layer: Controllers, CLI, HTTP Endpoints ]
                   │
                   ▼ (Invokes)
[ Domain Service / Use Case Interactor ]
                   │
                   ▼ (Depends on abstraction)
[ Domain Port Interface (<<Interface>>) ]
                   ▲
                   │ (Implements)
[ Infrastructure Adapter / In-Memory Fake (<<Fake>>) ]
```

- **Domain Isolation:** Entities, value objects, and domain services must have zero imports from external frameworks (no ORMs, no HTTP clients, no UI libraries).
- **Dependency Inversion:** High-level policy modules must never depend on low-level persistence or transport modules. Both depend on abstract Port interfaces.
- **Test Double First:** For every Port interface, specify an in-memory test double (`<<Fake>>` or `<<Mock>>`) enabling fast, deterministic AAA unit tests in Phase 2.

---

## 2. Mandatory Dual Visual Modeling (Mermaid.js)

Every SDD blueprint **MUST** contain both diagram models:

### 2.1. Technical Execution Flow (`sequenceDiagram`)
- Traces execution across layers: `Caller -> Controller -> Domain Service -> Port -> Adapter/Fake`.
- **Mandatory Syntax Rules:**
  - Must include `autonumber`.
  - All participant labels and message texts containing spaces, parentheses, or symbols **MUST be enclosed in double quotes** (`"..."`).
  - Must visualize both success flows and error branches (`alt / else`).

```mermaid
sequenceDiagram
    autonumber
    participant Client as "Client / Caller"
    participant API as "Controller / Entrypoint"
    participant Service as "Domain Service"
    participant Port as "Repository Port"
    
    Client->>API: "POST /resource (RequestDTO)"
    API->>Service: "execute(dto)"
    Service->>Port: "find_by_unique_key(key)"
    Port-->>Service: "None (Available)"
    Service->>Port: "save(entity)"
    Port-->>Service: "persisted_entity"
    Service-->>API: "ResponseDTO"
    API-->>Client: "HTTP 201 Created (ResponseDTO)"
```

### 2.2. Component & Contract Structure (`classDiagram`)
- Specifies class names, method signatures with typed arguments and returns, and relationships.
- Annotate Port interfaces with `<<Interface>>`.
- Annotate in-memory test doubles with `<<Fake>>` or `<<Mock>>`.

```mermaid
classDiagram
    direction TB

    class UserController {
        +register_user(req: UserCreateRequest) UserResponseDTO
    }

    class UserService {
        -repo: IUserRepository
        +register_user(req: UserCreateRequest) UserResponseDTO
    }

    class IUserRepository {
        <<Interface>>
        +save(user: User) User
        +find_by_email(email: str) User
    }

    class InMemoryUserRepository {
        <<Fake>>
        -_items: dict
        +save(user: User) User
        +find_by_email(email: str) User
    }

    UserController --> UserService : invokes
    UserService --> IUserRepository : depends on
    InMemoryUserRepository ..|> IUserRepository : implements
```

---

## 3. Typed Contracts & Boundary Schemas

Define typed request, response, and entity models using language-native schemas (e.g., Pydantic in Python or Zod in TypeScript):
- Map required fields, optional fields with defaults, and strict validation constraints.
- Define typed business exceptions (e.g., `DuplicateEntityError`, `EntityNotFoundError`).
- Represent contracts in pure YAML using [`resources/sdd-contract-template.yaml`](../resources/sdd-contract-template.yaml).

---

## 4. File Impact Analysis Matrix

Before code changes are made in Phase 2, classify every anticipated file alteration:

| File Path | Change Type | Risk Level | Description & Rationale |
|---|---|---|---|
| `src/domain/entities.py` | Additive (New) | Low | Core business entity model |
| `src/domain/ports.py` | Additive (New) | Low | Persistence and notification abstract interfaces |
| `src/services/user_service.py` | Additive (New) | Medium | Business logic orchestration |
| `src/api/routes.py` | Mutative (Edit) | Medium | Mount new endpoint route |

---

## 5. Automated Validation Gate

Validate the completed SDD artifact using the validator script:
```bash
python skills/plan/scripts/validate_sdd_contracts.py 01-concepcao/sdd-[slug].md
```
- **Validation Script:** [`scripts/validate_sdd_contracts.py`](../scripts/validate_sdd_contracts.py)
- **Contract Schema Template:** [`resources/sdd-contract-template.yaml`](../resources/sdd-contract-template.yaml)
- **Concrete Reference Example:** [`examples/plan-example.md`](../examples/plan-example.md)
