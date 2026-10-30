# Technical Documentation Guidelines (`references/docs-guidelines.md`)

Standards for Phase 5 (`/docs`). Template: [`../resources/doc-template.md`](../resources/doc-template.md). Walkthrough: [`../examples/docs-example.md`](../examples/docs-example.md).

## 1. Directives & Quality Gates

| Directive | Invariant & Rule | Scope / Command |
| :--- | :--- | :--- |
| **Reality-First** | Document actual running code and behavior only. | All READMEs & docstrings |
| **Manifests** | Validate commands against manifests (`pyproject.toml`, `package.json`, `Cargo.toml`, `Makefile`). | Onboarding docs |
| **Non-Destructive** | Edits limited to docstrings/comments/typing. Zero logic changes. | Source files |
| **Syntax Guard** | Verify zero regression after edits. | `python -m pytest -q` (Exit 0) |
| **Mermaid** | Double-quote node labels (`A["Client"] --> B["Service"]`). Direction: `TD` or `LR`. | Module `README.md` |

## 2. In-Code Docstrings (`Ref: Obsidian note [[sdd-[slug]]]`)

```python
def refund(tx_id: str, amount_cents: int) -> RefundResult:
    """Idempotent refund. Ref: Obsidian note [[sdd-[slug]]]"""
```
```typescript
/** Idempotent refund. Ref: Obsidian note [[sdd-[slug]]] */
function refund(txId: string, amountCents: number): RefundResult;
```

## 3. Governance & Changelog

| Standard | Directive | Format / Command |
| :--- | :--- | :--- |
| **Changelog** | Keep a Changelog (SemVer 2.0.0): `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`. | `### Added`<br>`- Implemented PaymentGatewayAdapter. (Ref: [[sdd-[slug]]])` |
| **Living DoD** | Mark documentation complete in `01-concepcao/dod-[slug].md`. | `- [x] Technical documentation updated via /docs (READMEs and docstrings).` |
| **Commit & Freeze** | Stage docs/sources; record semantic commit; seal feature branch. | `git commit -am "docs(feature): technical documentation and docstrings for [slug]"` |
