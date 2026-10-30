# Evolutionary Slicing & Task Decomposition Protocol (`references/decompose-protocol.md`)

Governs decomposition of epics into atomic, evolutionary task sequences.

## 1. Principles, Sizing & Slug Sanitization

| Dimension | Directive & Invariants |
| :--- | :--- |
| **5 Principles** | **1. Verifiable:** Observable behavior or enabler.<br>**2. Compatible:** Monotonic ($N+1$ extends $N$); zero contract breakage; layer slicing prohibited.<br>**3. Explicit Boundaries:** Typed contracts (`IRepository`, `IClient`) with first consumer; Fakes.<br>**4. Incremental Integration:** Merge into `develop` under CI; zero unmerged branch accumulation.<br>**5. Single-Chat:** Scope to one chat lifecycle; split if > 5 classes or multiple domains. |
| **Sizing** | **`[S]`** (1-2 files): Entity, VO, utility; zero external deps.<br>**`[M]`** (3-5 files): Standard use case, orchestration, adapter with Fake. Target single-chat size.<br>**`[L]` / `[XL]`** (6+ files): **PROHIBITED in final plan.** Split into `[S]` or `[M]`.<br>**`[SPIKE]`** ($S \le 2\text{h}$): Timebox for unknown library, API, or performance risk. |
| **Split Triggers** | Mandatory split if task touches domain + infra, requires > 3 DB migrations, or mixes happy path with complex errors. |
| **Slug Sanitization** | **Strict Regex:** `^[a-z0-9]+(-[a-z0-9]+)*$` (lowercase alphanumeric + single hyphens only). Applies to `epic-[slug].md` filenames, `epic_slug` frontmatter, and `feature/[slug]` checkout recommendations to prevent path traversal (`../`) and shell metacharacter injection (`;`, `&`, `|`, `$`, `` ` ``). Enforced by [`validate_dag.py`](../scripts/validate_dag.py). |

## 2. Architecture Tiers & DAG Verification

| Tier / Check | Technical Specification |
| :--- | :--- |
| **Batches** | **Batch 1 (Core):** Entities, VOs, exceptions, interfaces (zero I/O, network, DB deps).<br>**Batch 2..N-1 (App):** Use cases, domain services (depends on Batch 1; Fakes).<br>**Batch N (Infra):** Adapters (SQLAlchemy, HTTP, Kafka), controllers, DI (real integration tests). |
| **Pre-Flight Gate** | Execute `python skills/decompose/scripts/validate_dag.py 01-concepcao/epic-[slug].md --slug [slug]` (`graphlib.TopologicalSorter` cycle check, `[S]`/`[M]` sizing check, contract topological order, slug regex) **before** invoking `goldfish-dag-auditor` (`MaxIterations: 3`). |
| **Refs** | [`decompose-debate.md`](./decompose-debate.md) \| [`decompose-subagents.md`](./decompose-subagents.md) \| [`validate_dag.py`](../scripts/validate_dag.py) \| [`task-template.md`](../resources/task-template.md) \| [`decompose-example.md`](../examples/decompose-example.md). |
