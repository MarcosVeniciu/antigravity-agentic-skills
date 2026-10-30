---
name: test-fix
description: Surgically debugs test failures from terminal stack traces, isolates root causes in 1 sentence, and applies minimal fixes to production code.
---

# Skill: Reactive Test Failure Diagnosis & Surgical Remediation (`/test-fix`)

| Invariant | Operational Rule |
| :--- | :--- |
| **Direct Mode** | Direct execution in Orchestrator (0 subagents). |
| **Test Inviolability** | Never alter test assertions. Fix belongs strictly in `src/`. |
| **Surgical Scope** | Minimal diff addressing defect mechanism; zero refactoring. |
| **Double-Strike Limit** | Max 2 attempts. Strike 2 triggers hard reset and `/debug`. |

---

## Execution Pipeline

| Step | Directive | CLI / Actions | Refs |
| :--- | :--- | :--- | :--- |
| **1. Ingest** | Capture test node, exception, bottom frame. Isolated test if truncated. | `python -m pytest <test_file> -k <test_name> -vv --tb=short` | [`test-fix-protocol.md`](./references/test-fix-protocol.md) |
| **2. Triage & RCA** | Classify defect. Synthesize 1-sentence RCA per [`diagnostic-report-template.md`](./resources/diagnostic-report-template.md). | Formula: `[Category]: [Component] fails because [mechanism], causing [failure].` | [`diagnostic-report-template.md`](./resources/diagnostic-report-template.md) |
| **3. Surgical Fix** | Minimal fix in `src/`. Double-Strike rule (Strike 2 -> abort, reset, escalate). | `python -m pytest <test_file> -k <test_name> -v`<br>Abort: `git reset --hard HEAD && git clean -fd` | [`test-fix-protocol.md`](./references/test-fix-protocol.md), [`test-fix-example.md`](./examples/test-fix-example.md) |
| **4. Checkpoint** | Full regression check. Commit. | `git add <files>`<br>`git commit -m "checkpoint(test-fix): <failure>"` | [`test-fix-protocol.md`](./references/test-fix-protocol.md) |
