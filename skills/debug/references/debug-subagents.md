# Forensic Subagents, Isolation & Drift Gate

Specifications for context-isolated probing subagents and SDD Drift validation per [`debug-methodology.md`](./debug-methodology.md).

## 1. Subagent Specification (`forensic-prober`)

| Field | Configuration |
| :--- | :--- |
| **TypeName / Model** | `forensic-prober` / `"inherit"` |
| **Write Tools** | `true` (restricted to temporary probing scripts; `src/` modification strictly forbidden) |
| **SystemPrompt** | Role: Forensic Hypothesis Prober & 5 Whys Investigator. References: [`debug-methodology.md`](./debug-methodology.md), [`rca-template.md`](../resources/rca-template.md). Execute Step 2 of `/debug`: (1) Formulate competing hypotheses ($H_1, H_2$) without repeating falsified `/test-fix` hypotheses. (2) Write and run isolated probing tests or MRE scripts to confirm or falsify $H_1, H_2$. (3) Purge all scratch/probing files so `git status --short` remains clean. (4) Derive strict 5 Whys chain where Why #5 identifies automated test escape mechanism. (5) Formulate Option A (Surgical Fix) vs Option B (Architectural Alternative) and regression test design. Return structured Markdown report. Zero production edits. |

---

## 2. SDD Contract Drift Gate & Technical Pivots

| Action | Target / Command | Rule |
| :--- | :--- | :--- |
| **SDD Drift Gate** | `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <modified_src_files> --batch --pivots 02-auditorias/pivots-[slug].md` | Deterministic AST check; exit 0 required. |
| **Pivot Governance** | Record in `02-auditorias/pivots-[slug].md` via `@obsidian` | Mandatory prior to drift check if fix alters public contracts or signatures. |
