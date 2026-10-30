# Technical Documentation Guidelines (`references/docs-guidelines.md`)

Standards for Phase 5 (`/docs`). Template: [`../resources/doc-template.md`](../resources/doc-template.md). Walkthrough: [`../examples/docs-example.md`](../examples/docs-example.md). AST Validator: [`../scripts/verify_docstring_only.py`](../scripts/verify_docstring_only.py).

## 1. Directives & Quality Gates

| Directive | Invariant & Rule | Scope / Command |
| :--- | :--- | :--- |
| **Reality-First** | Document actual running code and behavior only. Never expose real `.env` secrets/tokens (`[QW-DOC-02]`). | All READMEs & docstrings |
| **Manifest Command Allowlist (`[DOC-LLM04-04]`)** | Validate commands against manifests (`pyproject.toml`, `package.json`, `Cargo.toml`, `Makefile`). Only transcribe standard package manager commands (`pip install`, `poetry install`, `pytest`, `npm ci`, `cargo build`) into `Getting Started`, flagging suspicious custom shell `curl`/`wget` pipes. | Onboarding docs |
| **Non-Destructive (`[DOC-ASI03-01]`)** | Edits limited strictly to docstrings/comments. Zero AST executable logic drift. | `python skills/docs/scripts/verify_docstring_only.py <modified_py_files>` |
| **Static Syntax Guard (`[DOC-ASI05-02]`)** | Use zero-RCE static compilation + AST/git diff verification instead of dynamic `pytest -q`. | `python -m py_compile <modified_python_files>` & `git diff <modified_py_files>` (Exit 0) |
| **Public Schema Exception (`[DOC-ASI09-03]`)** | Do NOT inject internal Obsidian wikilinks (`[[sdd-...]]`) into public FastAPI route docstrings, Pydantic models, or Typer/Click CLI help docstrings where they would leak into public OpenAPI/Swagger schemas or CLI help output. | FastAPI / Typer / Click / Pydantic |
| **Mermaid** | Double-quote node labels (`A["Client"] --> B["Service"]`). Direction: `TD` or `LR`. | Module `README.md` |

## 2. In-Code Docstrings (`Ref: Obsidian note [[sdd-[slug]]]`)

For internal domain/service/adapter functions and classes:
```python
def refund(tx_id: str, amount_cents: int) -> RefundResult:
    """Idempotent refund. Ref: Obsidian note [[sdd-[slug]]]"""
```
```typescript
/** Idempotent refund. Ref: Obsidian note [[sdd-[slug]]] */
function refund(txId: string, amountCents: number): RefundResult;
```
*Exception (`[DOC-ASI09-03]`):* For public FastAPI routes (`@app.get`, `@router.post`), Pydantic schemas, or Typer/Click CLI entrypoints, preserve clean OpenAPI/CLI descriptions and omit `Ref: Obsidian note [[sdd-[slug]]]` from the runtime-inspected docstring (place traceability in module `README.md` or `# Ref: [[sdd-[slug]]]` code comments instead).

## 3. Governance & Changelog

| Standard | Directive | Format / Command |
| :--- | :--- | :--- |
| **Changelog** | Keep a Changelog (SemVer 2.0.0): `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`. | `### Added`<br>`- Implemented PaymentGatewayAdapter. (Ref: [[sdd-[slug]]])` |
| **Living DoD** | Mark documentation complete in `01-concepcao/dod-[slug].md`. | `- [x] Technical documentation updated via /docs (READMEs and docstrings).` |
| **Commit & Freeze (`[QW-DOC-03]`)** | Stage docs/sources explicitly (never `git commit -am` or `git add .`); record semantic commit; seal feature branch. | `git add README.md <doc_files> && git commit -m "docs(feature): technical documentation and docstrings for [slug]"` |
