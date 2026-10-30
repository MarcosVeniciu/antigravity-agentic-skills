# Definition of Done Governance: Conception Phase (`references/plan-dod.md`)

Living DoD setup and Phase Gate 1 verification via [`plan-template.md`](../resources/plan-template.md).

## 1. Lifecycle SSOT & Phase Gate 1 Checklist (`01-concepcao/dod-[slug].md`)

| Item / Phase | Gate Criteria & Acceptance Targets | Tool / Script |
| :--- | :--- | :--- |
| **Phases 1–5** | 1: Plan (`[x]`). 2: Implement (exit `0`). 3: Refactor ($V(G) \le 10$). 4: Review (5 approvals). 5: Docs (updated). | [`plan-goldfish.md`](./plan-goldfish.md) |
| **Release** | Gatekeeper: zero unchecked items (`- [ ]`). | Release check |
| **1.1 Scope** | End-State defined; interview complete; Proposal approved. | `ask_question` |
| **1.2 Branch** | Branch created (`feature/[slug]`, `fix/[slug]`); base locked. | [`validate_branch.py`](../scripts/validate_branch.py) |
| **1.3 BDD** | Pure Gherkin (`@happy-path`, `@unhappy-path`, `@security`, `@concurrency`). | `bdd-[slug].md` |
| **1.4 SDD** | Sequence (quoted, autonumber, `alt/else`) + Class (parity, ports, fakes). | [`validate_sdd_contracts.py`](../scripts/validate_sdd_contracts.py) |
| **1.5 Goldfish** | 3x Flash subagents (`yagni`, `adversary`, `implementer`); Arbitration resolved. | Council audit |
| **1.6 Commit** | `dod-[slug].md` initialized via [`plan-template.md`](../resources/plan-template.md); Mode 3 semantic commit. | `git commit` |
