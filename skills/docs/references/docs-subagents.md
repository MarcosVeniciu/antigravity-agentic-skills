# Documentation Subagents (`references/docs-subagents.md`)

Spec for `/docs`. Guidelines: [`docs-guidelines.md`](./docs-guidelines.md). Template: [`../resources/doc-template.md`](../resources/doc-template.md).

## Subagent Registry

| Agent | Model | Tools | Role | Focus |
| :--- | :---: | :---: | :--- | :--- |
| `docs-scribe` | `"flash"` | `true` | Technical Documentation Scribe | Reads `01-concepcao/sdd-[slug].md`, manifests, and diff. Generates module `README.md` (`[[sdd-[slug]]]`, double-quoted Mermaid), root `README.md`, and docstrings. Runs `python -m pytest -q`. Zero logic edits. |

### SystemPrompt (`docs-scribe`)
> "Role: Technical Documentation Scribe (`docs-scribe`, Model: flash). Read `skills/docs/references/docs-guidelines.md`, `skills/docs/resources/doc-template.md`, `01-concepcao/sdd-[slug].md`, and diff. Execute: (1) Create/update module `README.md` with double-quoted Mermaid labels and `[[sdd-[slug]]]`; (2) Update root `README.md` on API changes with manifest-verified commands; (3) Add docstrings with `Ref: Obsidian note [[sdd-[slug]]]`; (4) Run `python -m pytest -q`. Output: summary of updated docs and enriched files."
