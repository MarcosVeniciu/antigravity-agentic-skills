# Infrastructure Execution Walkthrough

Walkthrough for dependency verification, anti-slopsquatting web escalation, and environment remediation per [`../SKILL.md`](../SKILL.md), [`../resources/env-template.md`](../resources/env-template.md), [`../scripts/audit_dependencies.py`](../scripts/audit_dependencies.py), and [`../scripts/validate_env.py`](../scripts/validate_env.py).

## 1. Execution Trace

| Phase | Target | Action & CLI |
| :--- | :--- | :--- |
| **Pre-Check Deps** | Registry API | `python skills/infra/scripts/audit_dependencies.py --ecosystem pypi --check asyncpg==0.29.0 openai==1.14.0` -> `[PASS]`. |
| **Web Audit (If Flagged)** | `dependency-auditor` | If a package flags `[SLOPSQUATTING_RISK]` or `[NEEDS_WEB_AUDIT]`, dispatch `dependency-auditor` (`Model: "flash"`, `search_web`) to confirm official repo and module names. |
| **Add Deps** | `pyproject.toml` / `pubspec.yaml` | Pin verified versions (`asyncpg = "^0.29.0"`, `openai = "^1.14.0"` or `flutter pub add http`). |
| **Audit Import Parity** | `audit_dependencies.py` | `python skills/infra/scripts/audit_dependencies.py pyproject.toml --scan-imports src` -> `[PASS]`. |
| **Sync Template** | `.env.example` | Append `DATABASE_URL=postgresql://user:pass@localhost:5432/db` and `OPENAI_API_KEY=sk-proj-placeholder`. |
| **Audit Template** | `validate_env.py` | `python skills/infra/scripts/validate_env.py .env.example` -> `[PASS]`. |
| **Remediate .env** | `.env` | Fix unquoted whitespace (`DATABASE_URL="postgresql://..."`) and replace exposed key with placeholder. |
| **Audit Parity** | `validate_env.py` | `python skills/infra/scripts/validate_env.py --env .env --example .env.example` -> `[PASS]`. |
