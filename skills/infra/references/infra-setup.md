# Reference: Infrastructure Setup, Dependency Management & Secret Hygiene

This guide provides authoritative operational instructions for managing environment variables, container specifications, dependency manifests, and secret containment in accordance with [`../SKILL.md`](../SKILL.md).

---

## 1. Environment Variable Management

### The Dual File Architecture
- **`.env` (Private / Local):** Contains active local development secrets and configuration values. Must be listed in `.gitignore` and **NEVER** committed to Git.
- **`.env.example` (Public / Tracked):** Checked into Git. Serves as the Single Source of Truth for required environment keys. Contains only safe, non-sensitive placeholders.

### Syntactic Conventions
1. **Naming:** All variable names must use `UPPER_SNAKE_CASE` (e.g., `DATABASE_URL`, `JWT_SECRET`).
2. **Contextual Prefixing:** Group variables logically by service subsystem (`DB_`, `REDIS_`, `AUTH_`, `AWS_`).
3. **Quoting Values:** Values containing whitespace, symbols, or commas **must** be enclosed in quotes:
   - *Valid:* `APP_TITLE="Antigravity Agentic Platform"`
   - *Invalid:* `APP_TITLE=Antigravity Agentic Platform`
4. **Descriptive Placeholders:** Use clear, self-explanatory placeholders in templates:
   - *Valid:* `DATABASE_URL=postgresql://user:password@localhost:5432/app_db`
   - *Forbidden:* `DATABASE_URL=postgresql://admin:ProdSecretPass123!@192.168.1.50:5432/production`

---

## 2. Container & Dockerfile Security Hygiene

1. **Multi-Stage Builds:** Separate build dependencies (compilers, dev libraries) from lightweight production runtime stages.
2. **Non-Root Execution:** Explicitly declare a dedicated non-root user:
   ```dockerfile
   RUN groupadd -r appgroup && useradd -r -g appgroup -d /app appuser
   USER appuser
   ```
3. **Pinned Base Images:** Never use `:latest`. Pin major or minor versions on minimal distributions:
   ```dockerfile
   FROM python:3.11-slim
   ```
4. **No Secrets in Dockerfiles:** Never use `ENV` or `ARG` to bake passwords or private API tokens into image layers. Pass secrets at runtime via environment variables or secret managers.
5. **Enforce `.dockerignore`:** Ensure `.dockerignore` excludes:
   - `.git/`, `.env`, `node_modules/`, `__pycache__/`, `.venv/`, `*.pyc`, `tests/`

---

## 3. Dependency Management & Pinning

1. **Surgical Scope:** Add only packages requested. Do not execute broad upgrades of existing packages.
2. **Deterministic Locking:** Always generate and commit lockfiles (`poetry.lock`, `package-lock.json`, `pnpm-lock.yaml`).
3. **Version Pinning:** Pin dependencies to avoid breaking changes from upstream semantic drift:
   - Python: `fastapi = "^0.110.0"` or exact `pydantic == 2.6.4`
   - Node: `"express": "^4.19.2"`
4. **Vulnerability Scanning:** Periodically audit dependencies via:
   - Python: `pip-audit` or `safety check`
   - Node: `npm audit --omit=dev`

---

## 4. Secret Containment Heuristics

The multiplatform validator [`../scripts/validate_env.py`](../scripts/validate_env.py) scans files using regex heuristics:

| Pattern Category | Regular Expression | Risk Level |
|:---|:---|:---|
| **AWS Access Key** | `AKIA[0-9A-Z]{16}` | CRITICAL |
| **JSON Web Token (JWT)** | `eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}` | CRITICAL |
| **OpenAI API Key** | `sk-[a-zA-Z0-9]{32,}` or `sk-proj-[a-zA-Z0-9_-]{32,}` | CRITICAL |
| **Private Key Block** | `-----BEGIN[ A-Z_-]*PRIVATE KEY` | CRITICAL |
| **GitHub Token** | `gh[pousr]_[A-Za-z0-9_]{36,}` or `github_pat_[A-Za-z0-9_]{40,}` | CRITICAL |

If any critical match is found in `.env.example` or committed files, the script halts execution with exit code 1.

---

## 5. Execution Commands

```bash
# Validate template syntax and check for leaked secrets
python skills/infra/scripts/validate_env.py .env.example

# Validate local .env against .env.example (detecting missing variables)
python skills/infra/scripts/validate_env.py --env .env --example .env.example --strict
```
