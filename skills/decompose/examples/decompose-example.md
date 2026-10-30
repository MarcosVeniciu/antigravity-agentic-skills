# Walkthrough: Async Audit Log & Notification Decomposition (`examples/decompose-example.md`)

Phase 0 (`/decompose`) lifecycle for an asynchronous audit logging and notification initiative on a financial transaction service.

## 1. Trace & Slicing Roadmap

| Step / Feature | Size | Deps | Technical Decisions & Deliverables |
| :--- | :---: | :---: | :--- |
| **Alignment** | — | — | Goal: transfer audit events and async customer emails; latency < 150ms. Challenge: direct Kafka coupling is SPOF. Adopted Transactional Outbox pattern with decoupled polling relay. |
| **F1:** `feature/transfer-audit-events` | `[M]` | — | **B1 [S]:** `AuditEvent` VO, `IAuditOutboxRepository` (zero I/O).<br>**B2 [M]:** `TransferFundsUseCase` stages outbox event via in-memory fake.<br>**B3 [M]:** PostgreSQL outbox migration & SQLAlchemy adapter commits atomically with transfer. |
| **F2:** `feature/outbox-worker-relay` | `[M]` | F1 | **B1 [S]:** `IEventPublisher` interface + test spy.<br>**B2 [M]:** `OutboxRelayWorker` polls `SKIP LOCKED` batch $\le 100$, exponential backoff retry. |
| **F3:** `feature/notification-kafka-adapter` | `[M]` | F2 | **B1 [M]:** `KafkaEventPublisher` implementing `IEventPublisher`.<br>**B2 [M]:** Email consumer dispatches with masked accounts via `IEmailClient`. |

## 2. Audit Verification

`goldfish-dag-auditor` verifies roadmap: strict acyclic DAG confirmed (F1 $\rightarrow$ F2 $\rightarrow$ F3), zero `[L]` slices, single introducer for `IEventPublisher`. Returns `[PASS]: DAG_VERIFIED`.
