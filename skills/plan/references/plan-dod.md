# Definition of Done Governance Guide: Conception Phase (`plan-dod`)

This guide governs the initialization and maintenance of the Living Definition of Done (`01-concepcao/dod-[slug].md`) during Phase 1 (`/plan`).

---

## 1. The Role of the Living DoD

The Living Definition of Done is the **Single Source of Truth (SSOT)** for delivery completeness, tracking feature maturity across all 5 ephemeral chat phases:
- **Phase 1 (`/plan`):** Conception, BDD specifications, SDD contracts, and Living DoD initialization.
- **Phase 2 (`/implement`):** Dynamic batch execution timeline entries (`## 2. Development Timeline`).
- **Phase 3 (`/refactor`):** Feature-wide macro-refactoring and AST complexity audit (`## 3. Refactoring`).
- **Phase 4 (`/review`):** 5-domain specialized audits (`## 3. Specialized Audits`).
- **Phase 5 (`/docs`):** Documentation synchronization and feature branch freeze (`## 4. Documentation`).
- **Release Gate (`/release`):** 100% mathematical release gatekeeper; no feature merges into release branches with any unchecked box (`- [ ]`).

---

## 2. Phase 1 Checklist (Phase Gate 1)

Before Phase 1 can be concluded and handed over to Phase 2, verify that all Phase 1 items in `01-concepcao/dod-[slug].md` are checked:

- [ ] **1.1 Scope Consensus Achieved:**
  - Desired End-State clearly formulated.
  - Socratic interview completed via `ask_question` tool.
  - Architectural proposal selected and approved (`RequestFeedback: true`).
- [ ] **1.2 Git Flow Branch Isolated:**
  - Branch checked and verified via `scripts/validate_branch.py`.
  - Active branch is `feature/[slug]` or `feat/[slug]` (not on `main`, `master`, `develop`).
- [ ] **1.3 Behavioral BDD Scenarios Formulated:**
  - Happy Path scenario documented in pure Gherkin syntax without technical leakage.
  - Unhappy Paths (validation, boundary, security) fully covered.
  - Saved to `01-concepcao/bdd-[slug].md`.
- [ ] **1.4 Technical SDD Blueprint & Contracts Modeled:**
  - Mandatory Mermaid `sequenceDiagram` (autonumber, quoted messages).
  - Mandatory Mermaid `classDiagram` (interfaces, DTOs, fakes).
  - Typed input/output contracts defined.
  - File impact analysis table completed.
  - Verified via `scripts/validate_sdd_contracts.py`.
  - Saved to `01-concepcao/sdd-[slug].md`.
- [ ] **1.5 Living DoD Initialized:**
  - `01-concepcao/dod-[slug].md` populated with links to BDD, SDD, and NFR criteria.
- [ ] **1.6 Phase 1 Semantic Squash Commit Executed:**
  - `git commit -m "docs(conception): BDD, SDD, and DoD specifications for [slug]"`.

---

## 3. Standard Living DoD Template Structure

When initializing `01-concepcao/dod-[slug].md`, use the standardized structure provided in [`resources/plan-template.md`](../resources/plan-template.md#living-definition-of-done-setup).
