# Operational Guide: Context-Isolated SOLID Refactoring Subagent & Drift Gate (`references/refactor-subagents.md`)

This guide governs the **SDD 2.0 (Elephant & Goldfish)** multi-agent execution model during Phase 3 (`/refactor`), isolating iterative SOLID/Clean Code transformations, repeated `pytest` executions, AST complexity re-scans, and SDD Drift Gate checks inside a dedicated subagent (`solid-refactorer`) so the main conversation context window remains clean.

---

## 1. Why Isolate Step 3 (`Surgical Refactoring Loop`) in a Subagent?

During Phase 3 (`/refactor`), the agent iterates through multiple refactoring targets in `task_list.md` across `git diff develop...HEAD`. For each target, it edits production code, runs `ast_complexity.py`, runs `pytest tests/unit/ -v`, rolls back via `git reset --hard HEAD` if a test breaks, and commits micro-checkpoints.

Running 5–10 iterations of `pytest -v` and AST scans directly in the main chat floods the context window with repetitive test runner logs and intermediate code diffs. By delegating Step 3 to **`solid-refactorer`**, the Main Orchestrator only processes:
1. The initial baseline AST scan and `task_list.md` opportunity mapping (Steps 1–2).
2. The final consolidated **Refactoring Evidence Matrix** (`V(G) Before` vs. `V(G) After`), SDD Drift Gate clearance, Living DoD update, and Phase Squash Commit (Step 4).

---

## 2. Step 3 Subagent: `solid-refactorer` (`Model: "inherit"`)

Define and invoke `solid-refactorer` during Step 3 (`EnableWriteTools: true`, `Model: "inherit"`):

- **Configuration:**
  - `Name`: `"solid-refactorer"`
  - `EnableWriteTools`: `true`
  - `Model`: `"inherit"`
  - `Role`: `"SOLID & AST Complexity Refactoring Specialist"`
- **Inputs Provided by Orchestrator:**
  - Path to `task_list.md` containing the mapped refactoring targets.
  - Path to `01-concepcao/sdd-[slug].md` and `02-auditorias/pivots-[slug].md`.
  - Baseline output of `skills/refactor/scripts/ast_complexity.py`.
- **SystemPrompt:**
  > *"You are a Context-Isolated SOLID & Clean Code Refactoring Specialist (`solid-refactorer`). Read the refactoring backlog in `task_list.md`, `skills/refactor/references/solid-catalog.md`, `skills/refactor/references/refactor-git.md`, and `01-concepcao/sdd-[slug].md`. Execute the guarded refactoring loop for each target: (1) Apply SOLID and Clean Code transformations strictly to production code without altering public SDD contracts or weakening test assertions; (2) Re-scan with `python skills/refactor/scripts/ast_complexity.py <file> --threshold 10` to confirm V(G) <= 10 and zero asymptotic warnings; (3) Run `python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <modified_files> --batch --pivots 02-auditorias/pivots-[slug].md` to ensure zero public contract drift; (4) Run `python -m pytest tests/unit/ -v`; (5) If any test fails or SDD drift occurs, revert immediately (`git reset --hard HEAD`) and apply the Double-Strike Rule (max 2 attempts per target); (6) On 100% green pass, record a micro-checkpoint (`git add <files> && git commit -m 'checkpoint(refactor): ...'`) and mark `[x]` in `task_list.md`. Return the completed Refactoring Evidence Matrix table with exact V(G) Before, V(G) After, and Test/Drift status."*

---

## 3. Mandatory SDD 2.0 Drift Gate in `/refactor`

Because `/refactor` enforces **Strict Behavioral & Contract Preservation** (Invariant Rule #2), extracting private helpers or splitting internal classes must never break the public class/interface/method signatures specified in `01-concepcao/sdd-[slug].md`.

Both `solid-refactorer` (per target) and the Main Orchestrator (at Step 4 exit) verify contract preservation via:
```bash
python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <MODIFIED_PYTHON_FILES> --check-files --pivots 02-auditorias/pivots-[slug].md
```
