# Changelog

All notable changes to the **Antigravity Agentic Workflows** framework will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and adheres to [Semantic Versioning 2.0.0](https://semver.org/).

---

## Release Notes - v1.1.0 (2026-10-27)

### New Features
- `[feat: decompose]`: Added dedicated [`skills/decompose/references/decompose-debate.md`](skills/decompose/references/decompose-debate.md) establishing Outcome-Based Socratic inquiry, native `ask_question` tool usage, macro XY Problem elimination, and the Macro-Slicing Strategy Matrix (MVP-First, Contract-First, Strangler Fig).
- `[feat: core-protocol]`: Refactored [`prompts/gemini.md`](prompts/gemini.md) to establish **Active Co-Programming & Symbiotic Partnership** as the central directive (*"AI proposes, human orchestrates and approves"*). Enforced interactive `ask_question` tool usage and added `-C <path>` for resilient cross-platform Git execution.

### Refactoring & Improvements
- `[refactor: skills]`: Standardized YAML frontmatter descriptions across all 12 skills, removing redundant `Use via /...` suffixes and cleaning up rigid phase designations.
- `[refactor: docs]`: Updated root [`README.md`](README.md) to remove obsolete documentation paths and align directly with the self-sufficient Agent Skills architecture.

### Repository Hygiene
- `[chore: cleanup]`: Pruned legacy / duplicate documentation files in `docs/`, deleted orphan empty `workflows-skill/` directory, and updated [`.gitignore`](.gitignore) with comprehensive ignores for test caches (`.pytest_cache/`, `.coverage`, `.mypy_cache/`, `.ruff_cache/`), virtual environments (`.venv/`), ephemeral worktrees (`worktrees/`), and OS artifacts.

---

## Release Notes - `v1.0.0` (2026-10-26)

### New Features
- `[feat: skills]`: Complete migration from legacy workflows into 12 self-sufficient modern Agent Skills (`skills/`) complying with Google Antigravity 2.0 standards:
  - `ask`, `debug`, `decompose`, `docs`, `implement`, `infra`, `obsidian`, `plan`, `refactor`, `release`, `review`, and `test-fix`.
  - Enforced strict three-tiered package architecture across every skill: `references/` (operational documentation), `resources/` (pure unpopulated templates), and `scripts/` (cross-platform CLI tools).
- `[feat: audit-reports]`: Standardized forensic audit and traceability reporting templates based on formal international engineering standards:
  - **ISO 19011 & IEEE 829**: Added canonical 5-domain audit report template in `skills/review/resources/audit-report-template.md` featuring Executive Summary, Semaphore Traceability Matrix (🟢/🟡/🔴), Detailed Forensic Findings with clickable IDE links (`file:///...#Lxx`), and Remediation Checkpoints.
  - **NIST SP 800-86 & ISO 27037**: Enhanced `skills/debug/resources/rca-template.md` with Forensic Traceability & Hypothesis Matrix connecting stack traces directly to empirical evidence, 5 Whys, and Root Cause Isolation.
  - **ISO 19011 & Clean Architecture**: Added `skills/refactor/resources/refactor-report-template.md` for refactoring consolidation with AST complexity tracking ($V(G) \le 10$) and public contract invariance guarantees.
  - **IEEE 829 & ISO 29119 (RTM)**: Integrated Requirements Traceability Matrix into `skills/plan/resources/plan-template.md` linking BDD scenarios to SDD contracts and Living DoD gates.
  - **ISO 19011 Compliance Matrix**: Upgraded pre-release verification gate in `skills/release/resources/release-template.md` to a structured Quality & Verification Audit Sign-Off matrix.
  - **ISO/IEC/IEEE 29119-3**: Added `skills/test-fix/resources/diagnostic-report-template.md` for structured test failure triage, 1-sentence root cause derivation, and isolated verification plans.
- `[feat: validation]`: Automated integrity test suite (`tests/test_flow_skills_integrity.py` and `tests/skills/test_scanners.py`) validating directory separation, YAML frontmatter, 3rd-person descriptions, referential integrity (zero broken links and zero orphan assets), and script compilation across all 13 canonical skills.

### Breaking Changes
- `[breaking: architecture]`: Deprecated and permanently removed legacy `workflows/` directory and old 24 fragmented skill subdirectories in favor of the unified 12-skill architecture.

---

## Release Notes - `v0.9.0` (2026-09-09)

### New Features
- `[feat: architecture]`: Introduced standardized, mandatory dual-level UML modeling across the lifecycle:
  - **Macro Level (`plan-decompose`)**: Added mandatory Structural Domain Delta (`classDiagram`) with strict `<<Existing>>`, `<<New>>`, and `<<Modified>>` styling, and Macro Business Journey (`sequenceDiagram`) tracing end-to-end user journeys mapped to roadmap sub-features (`[F1]`, `[F2]`).
  - **Micro Level (`plan-sdd`)**: Mandated Technical Execution Flow (`sequenceDiagram`) across layers (API -> Service -> Port -> Adapter/Fake) and Component & Contract Structure (`classDiagram`) specifying DTOs, interfaces, and test doubles.
- `[feat: references]`: Added dedicated reference guides for modeling standards under `skills/plan-decompose/references/`:
  - `class_diagram_conventions.md`: Guidelines for conceptual domain modeling, delta stereotypes, and anti-patterns.
  - `sequence_diagram_conventions.md`: Guidelines for cross-boundary business flow, actor/subsystem tagging, and sub-feature mapping.

### Performance & Refactoring
- `[refactor: docs]`: Full markdown sanitization across all 74 skill and workflow files, eliminating decorative emojis and visual icons to optimize token consumption and AST parsing reliability for LLMs.
- `[refactor: formatting]`: Standardized status transition arrows to ASCII (`->`) and aligned all newly created references strictly to English.

### Breaking Changes
- *None. All changes are backward-compatible additions and structural enhancements.*

---

## Release Notes - `v0.8.0` (2026-09-06)

### New Features
- `[feat: decompose]`: Implemented macro-architecture epic decomposition workflow (`/decompose`) and evolutionary vertical slicing skill (`plan-decompose`) with comprehensive contracts and slice dependency graphing.
- `[feat: review]`: Implemented multi-domain architectural and security review workflows (`/review`) covering Architecture, Security (OWASP), Quality (AST complexity), Performance, and Resilience.
- `[feat: scanners]`: Added automated scanning scripts for review gates:
  - `check_arch_boundaries.py`: Detects layer violations and UI-to-Domain leakage across Python, TypeScript/JavaScript, and Dart/Flutter.
  - `ast_complexity.py`: Evaluates cyclomatic complexity $V(G) \le 10$, nesting depth, and Big-O asymptotic heuristics with isolated inner function scoping.
  - `scan_sinks.py`: Audits code for SQL/command injections, CORS misconfigurations, and redacts sensitive credentials in reports.
- `[feat: test suite]`: Added comprehensive unit test suite (`tests/skills/test_scanners.py`) ensuring 100% coverage and reliability for automated review scanners.
- `[feat: plan-debate]`: Formalized Socratic inquiry protocols and Outcome-Based Prompting in `skills/plan-debate` for architectural scope discovery.

### Bug Fixes
- `[fix: links]`: Fixed documentation paths and relative markdown links across workflow definitions and skill manuals.

### Performance & Refactoring
- `[refactor: workflows]`: Refactored `/plan`, `/decompose`, and `/review` workflows to enforce zero-reading-latency skill loading and progressive disclosure.

### Breaking Changes
- *None. All additions are backward-compatible with v0.7.0.*

---

## Release Notes - `v0.7.0` (2026-09-04)

### New Features
- `[feat: installer]`: Cross-platform installation scripts (`install.ps1`, `install.sh`, `install.bat`) with automated transactional backups, rollback, and uninstallation.
- `[feat: architecture]`: Minimalist agent workflows separated into specialized single-purpose operational skills with progressive disclosure.

---
*Release consolidated via Antigravity Agentic Workflows.*
