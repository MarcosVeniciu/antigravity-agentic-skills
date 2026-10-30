# Infrastructure Setup & Security Hygiene

Specifications per [`../SKILL.md`](../SKILL.md) and [`../resources/env-template.md`](../resources/env-template.md).

## 1. Environment & Container Architecture

| Domain | Invariant | Enforcement / Syntax |
| :--- | :--- | :--- |
| **`.env`** | Local dev only; strictly in `.gitignore`. | Never commit to VCS. Prohibit live secrets. |
| **`.env.example`** | SSOT template for required variables. | Checked into VCS; safe placeholders only. |
| **Containers** | Multi-stage build; non-root user; immutable tags. | `USER appuser`, pin `python:3.11-slim`, zero secrets. |
| **`.dockerignore`** | Context isolation. | Exclude `.git/`, `.env`, `node_modules/`, `__pycache__/`, `.venv/`. |

---

## 2. Dependency Management & Pinning

| Ecosystem | Manifest & Lockfile | Command / Audit Rule |
| :--- | :--- | :--- |
| **Python** | `pyproject.toml`, `poetry.lock` | `poetry add <pkg>` (pin exact/caret); audit: `pip-audit`. |
| **Node** | `package.json`, `package-lock.json` | `npm install --save-exact <pkg>`; audit: `npm audit --omit=dev`. |
| **Rust / Go** | `Cargo.toml`, `go.mod` | Pin explicit semver versions; commit lockfiles. |

---

## 3. Secret Patterns ([`validate_env.py`](../scripts/validate_env.py))

| Token Category | Regex Pattern | Severity |
| :--- | :--- | :--- |
| **AWS Key** | `AKIA[0-9A-Z]{16}` | CRITICAL |
| **JWT Token** | `eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}` | CRITICAL |
| **OpenAI Key** | `sk-[a-zA-Z0-9]{32,}` \| `sk-proj-[a-zA-Z0-9_-]{32,}` | CRITICAL |
| **Private Key** | `-----BEGIN[ A-Z_-]*PRIVATE KEY` | CRITICAL |
| **GitHub Token** | `gh[pousr]_[A-Za-z0-9_]{36,}` \| `github_pat_[A-Za-z0-9_]{40,}` | CRITICAL |
