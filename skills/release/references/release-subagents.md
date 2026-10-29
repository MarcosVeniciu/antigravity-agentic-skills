# Operational Guide: Context-Isolated Release Auditor & Changelog Scribe (`references/release-subagents.md`)

This guide governs the **SDD 2.0 (Elephant & Goldfish)** multi-agent execution model during `/release`, offloading Living DoD 100% checkbox audits (Step 1) and SemVer 2.0.0 commit classification + Changelog compilation (Step 3) to a fast, low-cost **`release-auditor`** subagent running on **`Model: "flash_lite"`**.

---

## 1. Why Offload Steps 1 & 3 to `Model: "flash_lite"`?

During a multi-feature release, the agent must read every `01-concepcao/dod-[slug].md` across all candidate features, inspect the full commit log (`git log`), classify commits into SemVer 2.0.0 precedence (`MAJOR > MINOR > PATCH`), and populate both `CHANGELOG.md` and `03-releases/changelog-v[VERSION].md`.

Because these tasks are strictly algorithmic and verified deterministically in Step 4 by [`scripts/validate_release.py`](../scripts/validate_release.py), delegating them to **`release-auditor` (`Model: "flash_lite"`)**:
1. Keeps bulky DoD files and multi-branch `git log` outputs out of the main orchestrator's context window.
2. Minimizes token cost using `flash_lite`.
3. Keeps critical Git branch merges, integration test runs, and annotated tag creation strictly under the Main Orchestrator's control (Steps 2 & 4).

---

## 2. Subagent Definition: `release-auditor` (`Model: "flash_lite"`)

Define `release-auditor` using `define_subagent` (`EnableWriteTools: true` strictly for updating `CHANGELOG.md` and `03-releases/changelog-v[VERSION].md`; **never** execute `git merge`, `git checkout`, or `git tag` inside the subagent):

- **Configuration:**
  - `Name`: `"release-auditor"`
  - `EnableWriteTools`: `true`
  - `Model`: `"flash_lite"`
  - `Role`: `"Living DoD Gatekeeper & SemVer Changelog Scribe"`
- **SystemPrompt:**
  > *"You are the Release Gatekeeper & SemVer Scribe (`release-auditor`, `Model: flash_lite`). Follow `skills/release/references/release-checklist.md` and `skills/release/resources/release-template.md`. You operate in two phases: (Phase A — Step 1 Entry Gate): Read all candidate `01-concepcao/dod-[slug].md` files and verify that 100% of checkboxes across Phases 1–5 are marked `[x]`. If a single `- [ ]` is found, return `[REJECTED]` with the exact file and line. (Phase B — Step 3 SemVer & Changelog): Analyze the merged commit headers, calculate the exact SemVer 2.0.0 version bump (`MAJOR`, `MINOR`, or `PATCH`), prepend the formatted release notes to `CHANGELOG.md`, and write the immutable snapshot to `03-releases/changelog-v[VERSION].md`. NEVER run `git merge`, `git checkout`, or `git tag`."*
