---
name: ask
description: Answers conceptual, architectural, and codebase inquiries in strictly read-only mode, delegating broad multi-file searches to the built-in research subagent (flash_lite) to prevent context pollution.
---

# Skill: Project Oracle (`/ask`)

| Invariant | Operational Rule |
| :--- | :--- |
| **Read-Only** | Zero file writes. Diagnostics only (`git log`, `git status`). |
| **Context Isolation** | 1–2 files: direct. > 2 files / Vault: `research` (`flash_lite`). |
| **Humility** | Zero guessing. Ground claims in code or Vault. Declare gaps. |

---

## Execution Pipeline

| Step | Directive | Refs |
| :--- | :--- | :--- |
| **1. Parse** | Extract symbols, error tokens, routes. Classify intent. | [`ask-sources.md`](./references/ask-sources.md) |
| **2. Route** | Set scope: Direct (1–2 files) vs Broad (> 2 files / Vault). | [`ask-sources.md`](./references/ask-sources.md) |
| **3. Evidence** | Direct: `view_file`. Broad: dispatch `research` (`flash_lite`). | [`ask-sources.md`](./references/ask-sources.md) |
| **4. Synthesize** | Output Summary, Vault Intent (`[[note]]`), Code, Gaps. | [`ask-example.md`](./examples/ask-example.md) |

---

## Subagent Specification (`research`)

| Field | Configuration |
| :--- | :--- |
| **TypeName / Model** | `research` / `"flash_lite"` (Read-only, `EnableWriteTools: false`) |
| **Tools** | `grep_search`, `find_by_name`, `view_file`, `search_vault` |
| **SystemPrompt** | Role: Codebase & Vault Scout. Scan query terms. Return citation table (`file:///path#Lxx-Lyy`, `[[note]]`) with 1-sentence finding. Zero file writes. |
