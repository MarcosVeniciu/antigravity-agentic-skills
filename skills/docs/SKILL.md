---
name: docs
description: Synchronizes technical documentation, module READMEs, architectural diagrams, and in-code docstrings via a cost-efficient Flash subagent with Obsidian vault traceability and Living DoD updates.
---

# Skill: Technical Feature Documentation & Feature Freeze (`/docs`)

Synchronizes living technical documentation via isolated subagent `docs-scribe` (`Model: "flash"`), updates Living DoD, and seals the feature branch under Feature Freeze. Walkthrough: [`docs-example.md`](./examples/docs-example.md).

## Execution Pipeline

| Step | Actor | Technical Directive & Invariants | Command / Artifact |
| :--- | :--- | :--- | :--- |
| **1. Scope** | Orchestrator | Resolve branch and diff; locate specs (`01-concepcao/{bdd,sdd,dod}-[slug].md`); extract verified commands from manifests (`pyproject.toml`, `package.json`, `Cargo.toml`, `Makefile`). | `git --no-pager branch --show-current`<br>`git --no-pager diff develop...HEAD --name-only`<br>[`docs-guidelines.md`](./references/docs-guidelines.md) |
| **2. Living Docs** | `docs-scribe` (`flash`) | Generate module `README.md` (double-quoted Mermaid, component table, `[[sdd-[slug]]]`); update root `README.md` on API/install changes; add docstrings (`Ref: Obsidian note [[sdd-[slug]]]`) with zero logic change. Run syntax guard. | [`docs-subagents.md`](./references/docs-subagents.md)<br>[`doc-template.md`](./resources/doc-template.md)<br>`python -m pytest -q` |
| **3. Freeze** | Orchestrator | Mark `- [x]` in `01-concepcao/dod-[slug].md` with event entry; stage files explicitly; record semantic commit; seal branch in Feature Freeze (zero merge to develop/main). | `git add README.md 01-concepcao/dod-[slug].md ...`<br>`git commit -m "docs(feature): technical documentation and docstrings for [slug]"` |
