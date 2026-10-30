# Software Design Description: Architecture & Contracts (`references/plan-sdd.md`)

Design modeling via `sdd-architect` ([`plan-goldfish.md`](./plan-goldfish.md)).

## 1. Clean Architecture & Parity Invariants

| Layer / Model | Directives & Semantic Parity Requirements |
| :--- | :--- |
| **1. Entrypoint** | Controllers, HTTP. Validates DTOs; calls Services. Zero business logic. |
| **2. Domain Service** | Use cases. Orchestrates rules; depends on Ports (`<<Interface>>`). Zero infra imports. |
| **3. Port Interface** | Abstract boundaries (`<<Interface>>`). Typed contracts for persistence/APIs. |
| **4. Adapter / Fake** | Adapters implement ports; fakes (`<<Fake>>`) enable zero-I/O unit tests. |
| **`sequenceDiagram`** | Include `autonumber`; labels with spaces **MUST be double-quoted** (`"..."`). `alt/else` for negative BDD. Solid arrows (`->>`) must match `classDiagram` methods. |
| **`classDiagram`** | Typed args/returns; annotate `<<Interface>>` and `<<Fake>>`. 100% parity with sequenceDiagram. Declare `*Error` exceptions. |

## 2. Contracts, Impact Analysis & Validation

| Dimension | Specification |
| :--- | :--- |
| **Contracts** | DTOs via [`sdd-contract-template.yaml`](../resources/sdd-contract-template.yaml); `*Error` map 1:1 to negative BDD. |
| **Impact Matrix** | **Additive (New)** (entities, ports, fakes) vs **Mutative (Edit)** (shared schemas, routes). |
| **Validation Gate** | `python skills/plan/scripts/validate_sdd_contracts.py sdd.md --bdd bdd.md` |

Refs: [`validate_sdd_contracts.py`](../scripts/validate_sdd_contracts.py) \| [`sdd-contract-template.yaml`](../resources/sdd-contract-template.yaml) \| [`plan-example.md`](../examples/plan-example.md).
