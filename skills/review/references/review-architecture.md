# Operational Guide: Architecture, Coupling & SDD Drift Audit

This guide governs the surgical audit of architectural boundary isolation, SDD 2.0 specification drift, layer coupling, Dependency Inversion (DIP), DTO boundaries, and cohesion across the git diff.

---

## Phase 0 — Automated Boundary & SDD Drift Checks (Priority Guide)

Run the boundary linter and the SDD 2.0 Drift Gate validator against modified files to rapidly identify known boundary violations and unauthorized specification deviations:
```bash
python skills/review/scripts/check_arch_boundaries.py <modified_files>
python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <modified_files> --check-files --pivots 02-auditorias/pivots-[slug].md
```

### Evaluation Protocol:
- Treat any `[VIOLATION]` or `UNAUTHORIZED SPEC DRIFT` as an immediate architectural investigation lead.
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

### 2. Paridade SDD <-> Código (Drift Gate) & Fronteiras de DTOs
- **Fidelidade ao Contrato SDD (`01-concepcao/sdd-[slug].md`):** Verify that every class, `<<Interface>>` port, public method signature, and domain exception (`*Error` / `*Exception`) matches the approved SDD blueprint (or has a documented technical pivot in `02-auditorias/pivots-[slug].md`).
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

## Phase 3 — Audit Report Format

When recording findings for `02-auditorias/audit-architecture-[slug].md`, instantiate [`../resources/audit-report-template.md`](../resources/audit-report-template.md) and populate the Forensic Traceability Matrix and detailed findings:

```markdown
| ID | File & Line | Architectural Principle | Primary Evidence / Tool | Severity | Status & Traceability |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `ARC-01` | `src/domain/order.py:14` | Layer Boundary Isolation | check_arch_boundaries.py | High | 🔴 **Non-Compliant** ([see Finding 1](#-finding-1-direct-orm-import)) |
| `ARC-02` | `src/services/order.py:30` | SDD Contract Parity | check_sdd_drift.py | High | 🔴 **Non-Compliant** ([see Finding 2](#-finding-2-missing-sdd-method)) |
```
