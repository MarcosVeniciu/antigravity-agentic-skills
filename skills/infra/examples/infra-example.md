# Infrastructure Execution Walkthrough

Walkthrough for dependency addition and defect remediation per [`../SKILL.md`](../SKILL.md), [`../resources/env-template.md`](../resources/env-template.md), and [`../scripts/validate_env.py`](../scripts/validate_env.py).

## 1. Execution Trace

| Phase | Target | Action & CLI |
| :--- | :--- | :--- |
| **Add Deps** | `pyproject.toml` | Pin `asyncpg = "^0.29.0"` and `openai = "^1.14.0"`. |
| **Sync Template** | `.env.example` | Append `DATABASE_URL=postgresql://user:pass@localhost:5432/db` and `OPENAI_API_KEY=sk-proj-placeholder`. |
| **Audit Template** | `validate_env.py` | `python skills/infra/scripts/validate_env.py .env.example` -> `[PASS]`. |
| **Remediate .env** | `.env` | Fix unquoted whitespace (`DATABASE_URL="postgresql://..."`) and replace exposed key with placeholder. |
| **Audit Parity** | `validate_env.py` | `python skills/infra/scripts/validate_env.py --env .env --example .env.example` -> `[PASS]`. |
