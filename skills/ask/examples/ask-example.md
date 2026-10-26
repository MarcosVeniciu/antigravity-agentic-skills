# Representative Ask Sessions: Project Oracle Walkthroughs

This document demonstrates representative consultative interactions under `/ask`, exhibiting grounded citations, source triangulation, and strict read-only boundaries.

---

## Scenario A: Architectural Policy Inquiry

### User Question:
> "What is our architecture policy regarding direct database access from domain entities, and how do we enforce it?"

### Agent Response:

Based on the core architectural conventions and automated linter configuration, here are the standards:

#### 1. Architectural Policy & Boundary Rules
Our system strictly enforces **Clean Architecture layer isolation**:
- Domain entities and use cases must be pure business logic and are strictly prohibited from importing ORMs (SQLAlchemy, Prisma), database drivers (psycopg2, asyncpg), HTTP clients, or UI frameworks.
- Persistence must always be inverted via interfaces (Dependency Inversion Principle) defined in the domain layer and implemented in `infrastructure/`.

This rule is formally documented in the architectural conventions:
- Core Conventions: `[[conventions]]`
- Architecture Decision Record: `[[adr-004-clean-architecture-boundaries]]`

#### 2. Automated Static Enforcement
Layer boundaries are automatically validated in Phase 4 (`/review`) by an AST boundary scanner:
- Script: `check_arch_boundaries.py#L45-L88` (`workflows-skill/review/scripts/check_arch_boundaries.py#L45-L88`)
- The scanner parses imports in `domain/` and `use_cases/`, failing with exit code 1 if unauthorized imports (`sqlalchemy`, `httpx`, `requests`) are detected.

---

## Scenario B: Implementation & Test Traceability Inquiry

### User Question:
> "How does password hashing work during user registration, and where are the edge cases tested?"

### Agent Response:

Based on a code trace of the authentication subsystem:

#### 1. Implementation Details
Password hashing uses **Argon2id** through the `PasswordHasher` infrastructure adapter:
- Interface Contract: `IPasswordHasher` (`src/domain/security/hasher.py#L12-L24`)
- Concrete Implementation: `Argon2PasswordHasher.hash_password()` (`src/infra/security/argon2_hasher.py#L30-L52`)
- Registration Orchestration: The use case hashes the plain password before persisting the `User` aggregate:
  `RegisterUserUseCase.execute()` (`src/use_cases/register_user.py#L40-L55`)

#### 2. Test Coverage & Edge Cases
The password hashing and registration flow is verified by two test suites:
- **Unit Suite (AAA with Mocks):** `tests/unit/use_cases/test_register_user.py#L22-L68`
  - Happy path registration.
  - Duplicate email collision raising `DuplicateUserException`.
  - Password complexity validation failure (too short / missing special characters).
- **Security Boundary Tests:** `tests/unit/infra/test_argon2_hasher.py#L15-L40`
  - Verification that plain passwords never match raw hashed strings.
  - Constant-time verification to prevent timing attacks.

#### 3. Specifications in Vault
- BDD Acceptance Scenarios: `[[bdd-user-registration]]`
- Architectural SDD Blueprint: `[[sdd-user-registration]]`

---

## Scenario C: Handling an Undocumented / Missing Feature

### User Question:
> "Can a user cancel a pending payment transfer via the REST API?"

### Agent Response:

Based on an exhaustive search of the codebase routes, use cases, and Obsidian specifications:

#### 1. Current System Capabilities
- The transfer API currently exposes only two endpoints:
  - `POST /api/v1/transfers` — Create and execute transfer (`src/api/routes.py#L28-L45`)
  - `GET /api/v1/transfers/{id}` — Query transfer status (`src/api/routes.py#L50-L62`)

#### 2. Documentation & State Machine Analysis
- In the SDD state machine (`[[sdd-transfer-service]]`), transfer status moves directly from `PENDING` $\rightarrow$ `COMPLETED` or `FAILED`.
- There is **no** `CANCELLED` state defined in the domain enum `TransferStatus` (`src/domain/transfer.py#L10-L15`).
- No cancellation use case or endpoint exists in the codebase.

#### 3. Recommended Next Steps
If payment transfer cancellation is required:
1. Open a new chat session.
2. Run `/plan` to design the cancellation BDD scenarios, compensation transactions, and SDD state transitions.
