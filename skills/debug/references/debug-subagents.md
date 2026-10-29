# Operational Guide: Context-Isolated Forensic Probing Subagent (`references/debug-subagents.md`)

This guide governs the **SDD 2.0 (Elephant & Goldfish)** multi-agent execution model during Phase `/debug`, isolating empirical hypothesis testing, temporary Characterization/Probing Tests, MRE scripts, and multi-traceback falsification runs inside a dedicated subagent so the main conversation context window remains unpolluted.

---

## 1. Why Isolate Step 2 (`Probing Tests & 5 Whys`) in a Subagent?

During forensic debugging of complex runtime crashes, race conditions, or escalations from `/test-fix`, the agent must formulate competing hypotheses ($H_1, H_2$), write temporary probing tests or MRE scripts, execute `pytest`, inspect stack traces, falsify dead-end hypotheses, and iterate until the defect is deterministically reproduced.

Executing this trial-and-error loop in the main conversation pollutes the context window with:
- Falsified hypothesis code and discarded test snippets.
- Verbose `pytest -vv` tracebacks and debug print outputs.
- Intermediate file reads across unaffected modules.

By delegating Step 2 to the **`forensic-prober`** subagent, the Main Orchestrator receives **only** the verified empirical evidence matrix and the 5 Whys chain required to build `root_cause_analysis.md` in Step 3.

---

## 2. Step 2 Subagent: `forensic-prober` (`Model: "inherit"`)

Define and invoke `forensic-prober` during Step 2 (`EnableWriteTools: true` strictly for temporary probing tests that are cleaned up before returning; **never** modify production code during Step 2):

- **Configuration:**
  - `Name`: `"forensic-prober"`
  - `EnableWriteTools`: `true`
  - `Model`: `"inherit"`
  - `Role`: `"Forensic Hypothesis Prober & 5 Whys Investigator"`
- **Inputs Provided by Orchestrator:**
  - Incident symptom summary, exception type, and stack trace.
  - Escalation context from `/test-fix` (if applicable: failing test node and the 2 already-falsified hypotheses).
  - Relevant SDD contract (`01-concepcao/sdd-[slug].md`) and historical pivots (`02-auditorias/pivots-[slug].md`).
- **SystemPrompt:**
  > *"You are a Context-Isolated Forensic Bug Investigator (`forensic-prober`). You are strictly forbidden from modifying production source code (`src/`). Your mission is to execute Step 2 of `/debug` (`skills/debug/references/debug-methodology.md`): (1) Formulate at least two competing hypotheses ($H_1, H_2$) that do not repeat any previously falsified `/test-fix` hypotheses; (2) Write and run isolated automated probing/characterization tests or MRE scripts to empirically confirm or falsify $H_1$ and $H_2$; (3) Delete any temporary scratch/probing files once evidence is captured so the working tree remains clean; (4) Derive the strict 5 Whys chain where Why #5 explicitly answers why existing automated tests failed to catch the defect; (5) Formulate Option A (Recommended Surgical Fix) and Option B (Architectural Alternative) along with the exact permanent regression test design. Return a structured Markdown report containing the Hypothesis Evaluation Matrix, the 5 Whys chain, Option A vs Option B, and the regression test code."*

---

## 3. Step 4 SDD Contract Drift Safeguard

When applying the approved surgical fix in Step 4:
1. If the fix operates within a feature governed by an SDD blueprint (`01-concepcao/sdd-[slug].md`), run the SDD Drift Gate validator after tests turn green:
   ```bash
   python skills/implement/scripts/check_sdd_drift.py 01-concepcao/sdd-[slug].md <modified_src_files> --batch --pivots 02-auditorias/pivots-[slug].md
   ```
2. Ensure any architectural pivot or contract adjustment approved in Step 3 is logged in `02-auditorias/pivots-[slug].md` before running the drift check.
