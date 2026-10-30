---
name: plan
description: Orchestrates architectural conception, outcome-based scope debate, Context-Zero BDD/SDD subagents, Goldfish Council blind reviews, and living DoD setup.
---

# Architectural Conception & Planning (`/plan`)

Phase 1 conception via scope debate, Context-Zero subagents, Goldfish Council, and Living DoD under Git Flow. Zero code in Phase 1. Outputs: `feature/[slug]`, `01-concepcao/bdd-[slug].md`, `sdd-[slug].md`, `dod-[slug].md`.

## Execution Pipeline

| Step / Gate | Actor | Technical Directive & Invariants | CLI / Tools & Refs |
| :--- | :--- | :--- | :--- |
| **1. Scope Debate** | `Orchestrator` | End-State ($S_1 \dots S_n$); eliminate XY Problem; Proposal Matrix (Pragmatic, Scalable, Hybrid; max 3); approval (`RequestFeedback: true`). | `ask_question`<br>[`plan-debate.md`](./references/plan-debate.md)<br>[`plan-template.md`](./resources/plan-template.md) |
| **2. Git Flow** | `Orchestrator` | Lock base branches; validate working branch (`feature/[slug]`, `fix/[slug]`); isolate via worktree if concurrent. | `git checkout -b feature/[slug]`<br>[`plan-git.md`](./references/plan-git.md)<br>[`validate_branch.py`](./scripts/validate_branch.py) |
| **3. BDD Modeling** | `bdd-architect`<br>(`inherit`, write) | Context-Zero: author pure Gherkin (`@happy-path`, `@unhappy-path`, `@security`, `@concurrency`); zero jargon; save `01-concepcao/bdd-[slug].md`. | [`plan-bdd.md`](./references/plan-bdd.md)<br>[`plan-goldfish.md`](./references/plan-goldfish.md) |
| **4. SDD Blueprint** | `sdd-architect`<br>(`inherit`, write) | Context-Zero: model sequenceDiagram (`quoted`, `alt/else`), classDiagram (`<<Interface>>`, `<<Fake>>`, 100% parity), contracts; save `01-concepcao/sdd-[slug].md`. | `validate_sdd_contracts.py sdd.md --bdd bdd.md`<br>[`plan-sdd.md`](./references/plan-sdd.md)<br>[`sdd-contract-template.yaml`](./resources/sdd-contract-template.yaml)<br>[`validate_sdd_contracts.py`](./scripts/validate_sdd_contracts.py) |
| **5. Goldfish Council** | `3x Flash` (read-only):<br>🐠 `goldfish-yagni`<br>🐠 `goldfish-adversary`<br>🐠 `goldfish-implementer` | Parallel blind review: yagni (speculative layers), adversary (race conditions/negative BDD), implementer (missing types/signatures). Arbitrate via `ask_question`. | [`plan-goldfish.md`](./references/plan-goldfish.md) |
| **6. DoD & Commit** | `Orchestrator` | Init `dod-[slug].md` (1.1–1.6 `[x]`). Commit: `git add 01-concepcao/ && git commit -m "docs(conception): BDD, SDD, DoD for [slug]"`. | [`plan-dod.md`](./references/plan-dod.md)<br>[`plan-example.md`](./examples/plan-example.md) |
