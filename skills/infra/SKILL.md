---
name: infra
description: Orchestrates environment diagnostics, package manifest maintenance, container configuration validation, and strict secret containment via /infra.
---

# Skill: Infrastructure, Dependencies & Environment Governance (`/infra`)

Safely orchestrates project infrastructure setups, container definitions (`Dockerfile`, `docker-compose.yml`), package manifest updates (`pyproject.toml`, `package.json`, `Cargo.toml`), and environment variable configurations without exposing credentials or altering production application code.

---

## Operational Scope & Invariant Guardrails

- **Execution Context:** Activated whenever new runtime dependencies, third-party libraries, container services, or environment configuration variables are introduced or updated.
- **Invariant Safety Guardrails:**
  1. **Strict Dependency Minimization (No Blind Upgrades):** Modify or add only libraries strictly required for the immediate technical objective. Running blind updates (e.g., `npm update`, `pip install --upgrade *`) is strictly prohibited.
  2. **Absolute Secret Containment:** Passwords, API tokens, JWTs, AWS credentials, and private cryptographic keys must never be committed to source control or left in template files.
  3. **Strict Environment Parity:** Whenever an environment variable is introduced, `.env.example` must be updated with safe descriptive placeholders and verified via `validate_env.py`.
  4. **Strict Infrastructure Isolation:** Operations are strictly confined to configuration files, dependency manifests, and Dockerfiles. Modifying domain business logic or application entities is strictly forbidden under `/infra`.

---

## Execution Pipeline in 4 Steps

```mermaid
flowchart TD
    Init["Activation (/infra)"] --> S1["<b>Step 1: Diagnostics & Manifest Discovery</b><br/>• Discover package manifests<br/>• Map Docker & compose files<br/>• Review vault conventions"]
    S1 --> S2["<b>Step 2: Manifest & Container Updates</b><br/>• Surgical dependency additions<br/>• Multi-stage Dockerfile setup<br/>• Non-root container privileges"]
    S2 --> S3["<b>Step 3: Environment & Secret Containment</b><br/>• Update .env.example with placeholders<br/>• Quote values with spaces<br/>• Run heuristic secret scans"]
    S3 --> S4["<b>Step 4: CLI Validation & Handover</b><br/>• Run validate_env.py<br/>• Confirm 0 syntax & security errors<br/>• Handover to /implement or /test-fix"]
```

### Step 1: Environment Diagnostics & Manifest Discovery

1. Discover existing dependency and container manifests present in the repository root:
   - Python: `pyproject.toml`, `requirements.txt`, `poetry.lock`
   - Node/TypeScript: `package.json`, `package-lock.json`, `pnpm-lock.yaml`
   - Rust/Go: `Cargo.toml`, `go.mod`
   - Containers: `Dockerfile`, `docker-compose.yml`, `.dockerignore`
2. Consult [`./references/infra-setup.md`](./references/infra-setup.md) for ecosystem-specific container and dependency hygiene rules.
3. Review project infrastructure conventions in `00-core-rules/conventions.md` via `@obsidian` if applicable.

### Step 2: Manifest & Container Configuration Validation

1. Apply minimal, surgical dependency updates:
   - For Python: `poetry add <package>` or append pinned version to `pyproject.toml`.
   - For Node: `npm install --save-exact <package>`.
2. Ensure container definitions adhere to security best practices:
   - Multi-stage builds separating build tooling from minimal production runtimes.
   - Non-root user execution (`USER appuser`).
   - Pinned base image tags (`python:3.11-slim`, `node:20-alpine`).
   - `.dockerignore` excludes `.git`, `.env`, and test artifacts.

### Step 3: Environment Synchronization & Secret Containment

1. If new environment variables are required, update `.env.example` using the standardized structure from [`./resources/env-template.md`](./resources/env-template.md).
2. Adhere strictly to the three golden environment rules:
   - **Never commit `.env`:** Keep real secrets in `.env` (ignored by `.gitignore`).
   - **Safe Placeholders:** Use descriptive mocks in `.env.example` (e.g., `DATABASE_URL=postgresql://user:password@localhost:5432/app_db`).
   - **Quoting Standards:** Any value containing spaces or special characters must be enclosed in double quotes.

### Step 4: CLI Validation & Handover

1. Execute the multiplatform Python environment validator to confirm syntactic integrity, variable parity, and zero exposed credentials:
   ```bash
   python workflows-skill/infra/scripts/validate_env.py .env.example
   ```
2. If verifying local development setup, validate `.env` against `.env.example`:
   ```bash
   python workflows-skill/infra/scripts/validate_env.py --env .env --example .env.example
   ```
3. Issue the standard phase completion handover notice:
   > **[NEXT STEP]** *"Environment and dependencies updated successfully! Proceed with the development lifecycle via `/implement` or validate changes using `/test-fix`."*

---

## Bundled References, Resources, Scripts & Examples

- **Operational Setup & Security Hygiene Guide:**
  - [`references/infra-setup.md`](./references/infra-setup.md) — Comprehensive reference for container configurations, dependency pinning, and secret containment heuristics.
- **Standardized Environment Template:**
  - [`resources/env-template.md`](./resources/env-template.md) — Pure template for clean, documented `.env.example` files.
- **Multiplatform CLI Utility:**
  - [`scripts/validate_env.py`](./scripts/validate_env.py) — Cross-platform Python validator converted from legacy Bash script, enforcing syntax, variable parity, quoting, and secret detection.
- **Concrete Walkthrough Example:**
  - [`examples/infra-example.md`](./examples/infra-example.md) — Step-by-step infrastructure walkthrough demonstrating manifest addition, environment linter execution, and defect remediation.
