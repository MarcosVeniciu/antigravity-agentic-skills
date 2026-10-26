# Agent & Skill Architecture: Antigravity IDE

The operational intelligence of the **Antigravity IDE** is grounded in strict separation of concerns (*Single Responsibility Principle - SRP*) and *Outcome-Based Prompting*. Instead of monolithic prompts vulnerable to hallucinations and context exhaustion, the architecture organizes the software engineering lifecycle into:

1. **Phase 0 (Macro-Architecture):** Evolutionary decomposition of epics into monotonic sub-features via `/decompose`.
2. **Feature Lifecycle (5 Phases in Ephemeral Chats):** Conception $\rightarrow$ TDD $\rightarrow$ Refactoring $\rightarrow$ Audits $\rightarrow$ Documentation.
3. **Publication Cycle (Release Pipeline):** E2E integration tests, SemVer calculation, Changelog generation, and Git Flow via `/release`.

---

## 🔀 Router vs. Skill Execution Architecture

To keep AI context clean and focused, the ecosystem divides responsibilities into two distinct layers:

1. **State Routers in `workflows/`**: Lightweight playbooks defining phase pipelines, strict constraints, success evidence, and standardized phase transition gates (**[NEXT STEP]**).
2. **Specialized Execution in `skills/`**: Atomic operational procedures, automated validation scripts (`ast_complexity.py`, `validate_branch.sh`, `validate_sdd_contracts.py`), and templates loaded on-demand via Progressive Disclosure.
3. **Living Execution Log & DoD (`01-concepcao/dod-[slug].md`)**: Dynamic document centralizing development timeline history and Definition of Done (DoD) criteria for functional, non-functional, audit, and release validation.

---

## 🗺️ Complete Antigravity Ecosystem Map

```mermaid
graph TD
    User((User))

    subgraph Macro [Phase 0: Macro-Architecture & Epics]
        Dec[Epic Decomposition <br> /decompose]
    end

    subgraph Chat1 [Phase 1: Conception & Architecture]
        Plan[BDD + SDD + DoD Planning <br> /plan]
    end

    subgraph Chat2 [Phase 2: Iterative TDD Development]
        Imp[TDD Loop Batch by Batch <br> /implement]
    end

    subgraph Chat3 [Phase 3: Consolidation Refactoring]
        Ref[Clean Code & SOLID <br> /refactor]
    end

    subgraph Chat4 [Phase 4: Specialized Audits]
        Rev[Diff-Based Audit Loop <br> /review]
    end

    subgraph Chat5 [Phase 5: Technical Feature Documentation]
        Docs[Docs & Docstrings <br> /docs]
    end

    subgraph Pub [Publication & Integration Cycle]
        Rel[Release & E2E Integration <br> /release]
    end

    subgraph Support [Support Agents]
        Ask[Oracle <br> /ask]
        Debug[Forensic <br> /debug]
        Fix[Reactive Debugger <br> /test-fix]
        Infra[Infra & Manifests <br> /infra]
    end

    %% Macro Relations
    User -->|Large Epic| Dec
    Dec -->|Generates Sub-Feature Graph| Plan

    %% Feature Cycle Relations
    User -->|Isolated Feature| Plan
    Plan ==>|BDD + SDD + DoD Saved| Imp
    Imp -->|Red ➔ Green per Context Batch| Imp
    Imp ==>|100% Batches Complete| Ref
    Ref -.->|Test Failure| Fix
    Fix -.->|Fixed & Green| Ref
    Ref ==>|Clean Code without Smells| Rev
    Rev ==>|5 Domains Audited & Approved| Docs
    Docs ==>|Feature Frozen & DoD 100%| Rel

    %% Publication
    Rel -->|SemVer Tag, Changelog & Git Flow Merge| User

    %% Support
    Support -.- User

    style Macro fill:#2d1b38,stroke:#b800ff,stroke-width:2px,color:#fff
    style Chat1 fill:#1b2838,stroke:#00d2ff,stroke-width:2px,color:#fff
    style Chat2 fill:#1b382b,stroke:#00ff88,stroke-width:2px,color:#fff
    style Chat3 fill:#351b38,stroke:#d200ff,stroke-width:2px,color:#fff
    style Chat4 fill:#381b28,stroke:#ff0088,stroke-width:2px,color:#fff
    style Chat5 fill:#382d1b,stroke:#ffaa00,stroke-width:2px,color:#fff
    style Pub fill:#1b3838,stroke:#00ffd5,stroke-width:2px,color:#fff
    style Support fill:#222,stroke:#888,stroke-width:1px,stroke-dasharray: 5 5,color:#fff
```

---

## 🎯 Phase & Workflow Deep Dive

### 1. Phase 0: Macro-Architecture & Epics ([`/decompose`](agentes/decompose.md))
When an architectural epic is too complex to fit safely into a single feature branch, `/decompose` aligns the core problem (*Outcome-Based*) and breaks scope down into an ordered roadmap of monotonic vertical sub-features (contracts first, zero destructive rework). Persists `01-concepcao/epic-[slug].md`.
* **Skills Used:** [`skills/plan-debate`](skills/plan-debate.md), [`skills/plan-decompose`](skills/plan-decompose.md), [`skills/obsidian`](skills/obsidian.md).

### 2. Phase 1: Conception & Architecture ([`/plan`](agentes/plan.md) - Chat 1)
Surgical scope discovery via Socratic interviewing (3-5 questions), Git Flow branch validation, pure Gherkin BDD behavioral specification, SDD architectural blueprint with typed contracts/mocks, and Living DoD initialization.
* **Skills Used:** [`skills/plan-debate`](skills/plan-debate.md), [`skills/git`](skills/git.md), [`skills/plan-bdd`](skills/plan-bdd.md), [`skills/plan-sdd`](skills/plan-sdd.md), [`skills/dod`](skills/dod.md).

### 3. Phase 2: Iterative TDD Development ([`/implement`](agentes/implement.md) - Chat 2)
Executes the TDD pipeline batch by batch. Each batch decomposes AAA unit tests (Red) and minimal SOLID production code (Green), running tests in the terminal with reactive debugging support, recording local checkpoints, and continuously appending history to the DoD timeline.
* **Skills Used:** [`skills/tdd-plan`](skills/tdd-plan.md), [`skills/tdd-tests`](skills/tdd-tests.md), [`skills/tdd-code`](skills/tdd-code.md), [`skills/test-fix`](skills/test-fix.md), [`skills/dod`](skills/dod.md), [`skills/git`](skills/git.md).

### 4. Phase 3: Consolidation Refactoring ([`/refactor`](agentes/refactor.md) - Chat 3)
Optimizes internal software design (*Make it Right*). Strictly restricted to files modified on the active branch (`git diff develop...HEAD`), eliminating cyclomatic complexity, long methods, and deep nesting through Guard Clauses and SOLID principles, keeping tests 100% green.
* **Skills Used:** [`skills/refactor`](skills/refactor.md), [`skills/git`](skills/git.md), [`skills/dod`](skills/dod.md), [`skills/test-fix`](skills/test-fix.md).

### 5. Phase 4: Specialized Audits ([`/review`](agentes/review.md) - Chat 4)
Iterative domain-specialized loop executed directly over the feature's `git diff` using a **Script-First** strategy and Call Hierarchy Taint Analysis, aligned with the [OWASP Code Review Guide v2](references/OWASP_Code_Review_Guide_v2.pdf):
1. **Architecture & Coupling** ([`skills/review-architecture`](skills/review-architecture.md) + `check_arch_boundaries.py`)
2. **Security & OWASP** ([`skills/review-security`](skills/review-security.md) + `scan_sinks.py`)
3. **Quality & AST Complexity** ([`skills/review-quality`](skills/review-quality.md) + `ast_complexity.py`)
4. **Performance & Volumetrics** ([`skills/review-performance`](skills/review-performance.md))
5. **Resilience & Fault Tolerance** ([`skills/review-resilience`](skills/review-resilience.md))
Each reviewed domain generates a local micro-checkpoint and updates the Living DoD via `skills/dod`. Detailed guide: [Review Agent Docs](agentes/review.md).

### 6. Phase 5: Technical Feature Documentation ([`/docs`](agentes/docs.md) - Chat 5)
Focuses strictly on technical documentation: updating module/root READMEs, adding docstrings with bidirectional links to the Obsidian Vault, marking the DoD, and committing semantically. The feature branch remains frozen and intact without premature merges.
* **Skills Used:** [`skills/docs`](skills/docs.md), [`skills/dod`](skills/dod.md), [`skills/git`](skills/git.md).

### 7. Publication Cycle: Integration & Release ([`/release`](agentes/release.md))
Orchestrates publication of a release on `release/vX.Y.Z` branched from `develop`. Audits 100% DoD completion across all candidate features, runs staged E2E integration test suites with formatted console banners ([`skills/test-integration`](skills/test-integration.md)), computes SemVer, generates `CHANGELOG.md`, and completes Git Flow with annotated tags and merges into `main` and `develop`.
* **Skills Used:** [`skills/test-integration`](skills/test-integration.md), [`skills/release`](skills/release.md), [`skills/dod`](skills/dod.md), [`skills/git`](skills/git.md).

---

## 🧰 [Modular Skills Catalog](skills/README.md)

Detailed guides, scripts, and procedures for all 24 skills:

| Category | Skills |
| :--- | :--- |
| **Macro & Conception** | [`skills/plan-decompose`](skills/plan-decompose.md), [`skills/plan-debate`](skills/plan-debate.md), [`skills/plan-bdd`](skills/plan-bdd.md), [`skills/plan-sdd`](skills/plan-sdd.md) |
| **TDD Construction** | [`skills/tdd-plan`](skills/tdd-plan.md), [`skills/tdd-tests`](skills/tdd-tests.md), [`skills/tdd-code`](skills/tdd-code.md), [`skills/test-fix`](skills/test-fix.md) |
| **Refactoring & Design** | [`skills/refactor`](skills/refactor.md) |
| **Specialized Audits** | [`skills/review-architecture`](skills/review-architecture.md), [`skills/review-security`](skills/review-security.md), [`skills/review-quality`](skills/review-quality.md), [`skills/review-performance`](skills/review-performance.md), [`skills/review-resilience`](skills/review-resilience.md) |
| **Documentation & Delivery** | [`skills/docs`](skills/docs.md), [`skills/test-integration`](skills/test-integration.md), [`skills/release`](skills/release.md) |
| **Support & Diagnostics** | [`skills/ask`](skills/ask.md), [`skills/debug`](skills/debug.md), [`skills/infra`](skills/infra.md) |

