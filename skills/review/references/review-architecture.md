# Operational Guide: Architecture & Coupling Audit

This guide governs the surgical audit of architectural boundary isolation, layer coupling, Dependency Inversion (DIP), DTO boundaries, and cohesion across the git diff.

---

## Phase 0 — Automated Boundary Check (Priority Guide)

Run the boundary linter against modified files to rapidly identify known boundary violations:
```bash
python workflows-skill/review/scripts/check_arch_boundaries.py <modified_files>
```

### Evaluation Protocol:
- Treat any `[VIOLATION]` as an immediate architectural investigation lead.
- **Critical:** Scanners prioritize reading but do NOT replace semantic architectural inspection. Always evaluate full class and module responsibilities across the diff.
- If a target contains non-standard directory structures or unmapped languages, document the limitation in the report.

---

## Phase 1 — In-Depth Code Inspection (Evidence Gathering)

### 1. Isolamento de Camadas & Inversão de Dependência (DIP)
- **Vazamento de Infraestrutura no Domínio:** Verify whether pure business layers (`domain/`, `entities/`, `use_cases/`) import:
  - Database drivers or ORMs (`sqlalchemy`, `typeorm`, `prisma`, `django.db`)
  - Web frameworks (`flask`, `express`, `fastapi`, `django`)
  - HTTP clients (`requests`, `httpx`, `axios`, `aiohttp`)
  - UI libraries (`package:flutter/material.dart`, `react`)
- **Dependências Ocultas:** Detect direct instantiation of network clients, external services, or concrete repositories inside constructors or business methods (`new HttpClient()`, `DatabaseConnection()`).
- **Injeção de Dependência:** Verify that use cases and domain services depend strictly on abstract interfaces/protocols injected via constructor (`__init__`), enabling isolated testability and loose coupling.

### 2. Fronteiras de DTOs & Contratos de Transporte
- **Exposição de Modelos Internos:** Ensure persistence entities (ORM models) or rich domain models are never returned directly across API boundary layers without an explicit DTO mapper.
- **Contratos Fortemente Tipados:** Verify that all inbound and outbound boundary payloads use immutable, validated schemas (Pydantic models, Python dataclasses, TypeScript interfaces).

### 3. Coesão & Princípio da Responsabilidade Única (SRP)
- **God Classes & Modulite:** Flag classes accumulating data parsing, validation rules, business logic, and persistence calls in a single monolithic structure.
- **Efeitos Colaterais & Mutabilidade Inesperada:** Identify in-place mutation of input arguments (`args.append(...)`, direct modification of caller dictionaries/lists). Enforce defensive copying where shared state risk exists.

---

## Phase 2 — Surgical Recommendations & Mitigation (Mode B Only)

- **Dependency Inversion:** Declare an abstract interface/protocol in the domain layer and inject the concrete adapter at the composition root:
  ```python
  # Before: tightly coupled
  class CheckoutService:
      def __init__(self):
          self.gateway = StripePaymentGateway()  # Direct instantiation
  
  # After: inverted via constructor injection
  class CheckoutService:
      def __init__(self, gateway: IPaymentGateway):
          self.gateway = gateway
  ```
- **DTO Decoupling:** Introduce boundary transfer objects between controller and domain layers:
  ```python
  # Domain entity stays isolated from HTTP JSON quirks
  order_dto = CreateOrderDTO.from_request(request.json)
  order = order_dto.to_domain()
  ```
- **Defensive Immutability:** Return copies or use frozen dataclasses (`@dataclass(frozen=True)`) to eliminate unwanted side effects.
- **Cohesive Extraction:** Slice oversized classes into single-purpose components (`OrderValidator`, `OrderCalculator`, `OrderRepositoryPort`).

---

## Phase 3 — Audit Report Table Format

When recording findings for `02-auditorias/audit-architecture-[slug].md`, use this standardized schema:

```markdown
| ID | File / Line | Architectural Principle | Severity | Confidence | Disposition | Impact / Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ARC-01` | `src/domain/order.py:14` | Layer Boundary Isolation | High | High | Confirmed | Domain entity imports SQLAlchemy Session directly |
```
