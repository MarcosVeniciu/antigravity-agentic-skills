# Operational Guide: Context-Isolated Documentation Subagent (`references/docs-subagents.md`)

This guide governs the **SDD 2.0 (Elephant & Goldfish)** multi-agent execution model during Phase 5 (`/docs`), delegating bulk module `README.md` authoring, Mermaid diagram formatting, and in-code docstring enrichment (`Ref: Obsidian note [[sdd-[slug]]]`) to a cost-efficient **`docs-scribe`** subagent running on **`Model: "flash"`**.

---

## 1. Why Offload Step 2 (`Living Documentation Updates`) to `Model: "flash"`?

During Phase 5 (`/docs`), all architectural design (`01-concepcao/sdd-[slug].md`), behavioral scenarios (`01-concepcao/bdd-[slug].md`), and code implementations are already finalized and audited.

Having the primary orchestrator model read every modified source file and generate markdown tables, Mermaid diagrams, and multi-line docstrings across the entire feature diff consumes high-tier reasoning quota and fills the main conversation context with full-file reads and edits.

Delegating Step 2 to **`docs-scribe` (`Model: "flash"`)**:
1. **Reduces Token Cost:** `Model: "flash"` excels at structured template population (`resources/doc-template.md`) and docstring synthesis from existing SDD contracts at a fraction of the cost.
2. **Isolates File Reads/Edits:** All intermediate source file reads and `edit_file` operations stay inside the subagent's context window.
3. **Guarantees Syntax Safety:** `docs-scribe` runs `python -m pytest -q` before finishing to prove that docstring insertions caused zero indentation or syntax regressions.

---

## 2. Step 2 Subagent: `docs-scribe` (`Model: "flash"`)

Define and invoke `docs-scribe` during Step 2 (`EnableWriteTools: true`, `Model: "flash"`):

- **Configuration:**
  - `Name`: `"docs-scribe"`
  - `EnableWriteTools`: `true`
  - `Model`: `"flash"`
  - `Role`: `"Technical Documentation & Docstring Scribe"`
- **Inputs Provided by Orchestrator:**
  - Active feature slug (`[slug]`) and list of modified files (`git diff develop...HEAD --name-only`).
  - Verified build/test/run commands extracted from project manifests (`pyproject.toml`, `package.json`, etc.).
  - Paths to `01-concepcao/bdd-[slug].md` and `01-concepcao/sdd-[slug].md`.
- **SystemPrompt:**
  > *"You are a Context-Isolated Technical Documentation Scribe (`docs-scribe`, `Model: flash`). Read `skills/docs/references/docs-guidelines.md`, `skills/docs/resources/doc-template.md`, `01-concepcao/sdd-[slug].md`, and the modified source files on this branch. Execute Step 2 of `/docs`: (1) Create or update module-level `README.md` files in modified directories with double-quoted Mermaid node labels, component mapping tables, and `[[sdd-[slug]]]` wikilinks; (2) Update root `README.md` only if onboarding commands or public subsystems changed, using strictly the manifest-verified commands; (3) Insert or enrich in-code docstrings in modified classes and functions including `Ref: Obsidian note [[sdd-[slug]]]` while NEVER altering control flow, expressions, return values, or indentation; (4) Run `python -m pytest -q` to verify that docstring edits introduced zero syntax or test regressions. Return a concise summary of all created/updated `README.md` files and enriched source files."*
