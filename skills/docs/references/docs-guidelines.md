# Technical Documentation Guidelines & Standards

This guide governs the operational standards, conventions, and quality gates for technical documentation generated during Phase 5 (`/docs`).

---

## 1. Core Principles of Living Documentation

1. **Reality-First Documentation:** Documentation must describe what the code actually does, not what was originally planned or hoped for. Always verify behavior against tests and production implementations.
2. **Manifest Verification Requirement:** Never document unverified, speculative, or fictitious commands.
   - For Python: Verify against `pyproject.toml`, `setup.cfg`, `requirements.txt`, or `Makefile`.
   - For Node.js/TypeScript: Verify against `package.json` (`scripts` section).
   - For Go: Verify against `go.mod` and `Makefile`.
   - For Rust: Verify against `Cargo.toml`.
3. **Strict Non-Destructive Code Edits:** When editing source files to add docstrings:
   - NEVER modify logic expressions, control flow (`if`/`else`, loops), variable definitions, or return values.
   - NEVER alter import statements unless adding typing imports (`from typing import ...`) required solely for documentation type annotations.
   - Run the test suite before and after adding docstrings to verify zero regression.
4. **Cross-Referencing Template:** Use the unified template provided in [`../resources/doc-template.md`](../resources/doc-template.md).
5. **Concrete Output Reference:** Consult [`../examples/docs-example.md`](../examples/docs-example.md) for a complete example.

---

## 2. Mermaid Diagram Standards

To ensure Mermaid diagrams render cleanly without syntax crashes across GitHub, GitLab, Obsidian, and IDE previews:
1. **Always Double-Quote Node Labels:**
   ```mermaid
   graph TD
       A["HTTP Controller / API Gateway"] --> B["Order Fulfillment Service"]
       B --> C["SQL Repository Adapter"]
   ```
2. **Avoid Reserved Characters:** Do not use unescaped braces, parentheses, or brackets inside node labels unless enclosed in quotes.
3. **Direction Conventions:**
   - Use `TD` (top-down) for layered architecture and hierarchical module decomposition.
   - Use `LR` (left-to-right) for data flow pipelines and state transitions.

---

## 3. In-Code Docstring Standards by Ecosystem

### 3.1. Python (PEP 257 & Google Style)
Include a one-line summary, detailed explanation (if necessary), argument descriptions, return values, exceptions raised, and the mandatory Obsidian reference tag:

```python
def process_refund(transaction_id: str, amount_cents: int) -> RefundResult:
    """
    Initiates and processes an idempotent refund transaction with the payment gateway.

    Args:
        transaction_id: Unique identifier of the original settled charge.
        amount_cents: Non-negative integer representing refund amount in cents.

    Returns:
        RefundResult containing gateway status, refund ID, and settlement timestamp.

    Raises:
        InvalidTransactionError: If transaction_id does not exist or charge is unsettled.
        GatewayTimeoutError: If upstream payment provider fails to respond.

    Ref: Obsidian note [[sdd-payment-gateway]]
    """
```

### 3.2. TypeScript / JavaScript (TSDoc / JSDoc)
```typescript
/**
 * Processes an idempotent refund transaction with the payment gateway.
 *
 * @param transactionId - Unique identifier of the original settled charge.
 * @param amountCents - Non-negative integer representing refund amount in cents.
 * @returns RefundResult containing gateway status and settlement timestamp.
 * @throws {InvalidTransactionError} If charge is unsettled.
 *
 * Ref: Obsidian note [[sdd-payment-gateway]]
 */
```

---

## 4. Architecture Documentation Standards

### 4.1. Module & Subdirectory READMEs
Every modified architectural package or module directory must maintain a local `README.md` structured with:
1. **Title & Purpose:** Clear, concise statement of the directory's architectural responsibility.
2. **Layer Classification:** Specify architectural tier (Domain Entity, Application Use Case, Infrastructure Adapter, External Interface).
3. **Data Flow & Architecture Diagram:** Mermaid diagram showing inputs, internal components, and outputs.
4. **Component Mapping Table:** Table listing files, roles, and public APIs.
5. **Design Decisions & Trade-offs:** Brief documentation of architectural choices made and alternatives discarded.
6. **Testing Strategy:** Types of tests covering the directory (Unit, Integration, Contract) and critical edge cases.
7. **Obsidian Traceability:** Wikilinks to related BDD, SDD, and ADR notes.

### 4.2. Root Project Showcase (`README.md`)
Updated only when a feature introduces new public endpoints, architectural subsystems, or changes onboarding commands:
- High-level business vision and problem solved.
- Tech stack overview with explicit runtime versions.
- Architecture diagram covering full system context.
- Copy-paste verified onboarding commands (prerequisites, installation, execution, test command).

---

## 5. Changelogs & Release Preparation

Phase 5 prepares feature changelog entries following the [Keep a Changelog](https://keepachangelog.com/) standard aligned with Semantic Versioning 2.0.0:

### 5.1. Standard Change Categories
- `Added`: New user-facing capabilities, public APIs, or architectural components.
- `Changed`: Modifications in existing functionality or contracts.
- `Deprecated`: Capabilities marked for upcoming removal.
- `Removed`: Capabilities or endpoints removed in this feature.
- `Fixed`: Bug fixes or defect remediation.
- `Security`: Vulnerability mitigations or hardening enhancements.

### 5.2. Feature Changelog Format
```markdown
### Added
- Implemented `PaymentGatewayAdapter` with automated circuit-breaker fallback. (`Ref: [[sdd-payment-gateway]]`)
```

---

## 6. Phase 5 Governance & Git Freeze Protocol

1. **Living DoD Update:**
   Open `01-concepcao/dod-[slug].md` and mark:
   ```markdown
   - [x] Technical documentation updated via /docs (READMEs and docstrings).
   ```
2. **Consolidation Commit:**
   Stage all modified files and commit with standard semantic format:
   ```bash
   git commit -am "docs(feature): technical documentation and docstrings for [slug]"
   ```
3. **Prohibition of Direct Merges:**
   - Under no circumstances should the agent merge `feature/[slug]` into `develop` or `main`.
   - The branch must remain isolated and clean for the integration testing and release tagging performed in `/release`.
