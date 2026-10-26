# Walkthrough Example: Environment Validation & Secret Remediation

This walkthrough demonstrates the execution of [`../SKILL.md`](../SKILL.md) when introducing a new PostgreSQL database service and OpenAI client, showing how [`../scripts/validate_env.py`](../scripts/validate_env.py) catches defects and verifies secret containment.

---

## 1. Scenario Context

A feature requires adding `asyncpg` and `openai` to the project.
The developer introduces:
1. `DATABASE_URL` for PostgreSQL.
2. `OPENAI_API_KEY` for AI completions.

---

## 2. Step 1: Manifest Updates

In `pyproject.toml`:
```toml
[tool.poetry.dependencies]
python = "^3.11"
asyncpg = "^0.29.0"
openai = "^1.14.0"
```

---

## 3. Step 2: Updating `.env.example`

Using [`../resources/env-template.md`](../resources/env-template.md), the developer appends variables to `.env.example`:
```env
# Database connection
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app_db

# OpenAI Integration
OPENAI_API_KEY=sk-proj-placeholder_key_here
```

---

## 4. Step 3: Running Validator on `.env.example`

```bash
python skills/infra/scripts/validate_env.py .env.example
```

**Output:**
```text
🔍 Validating template file: '.env.example'...
----------------------------------------------------------------------
✅ Environment validation COMPLETED SUCCESSFULLY! No syntax or security issues detected.
```

---

## 5. Step 4: Catching Defect & Secret Leak in Local `.env`

Suppose a developer creates a flawed local `.env`:
```env
# Defect 1: Unquoted space
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app db

# Defect 2: Accidental real API key committed or pasted
OPENAI_API_KEY=sk-abcdef1234567890abcdef1234567890abcdef1234
```

Running the parity and security check:
```bash
python skills/infra/scripts/validate_env.py --env .env --example .env.example
```

**Output:**
```text
🔍 Validating template file: '.env.example'...
🔍 Validating environment file: '.env'...
⚖️ Comparing '.env' against '.env.example'...
----------------------------------------------------------------------
❌ Validation FAILED! 2 Error(s) detected:
   [.env] [Line 2] Unquoted whitespace in 'DATABASE_URL'. Values containing spaces must be enclosed in quotes: DATABASE_URL="postgresql://postgres:postgres@localhost:5432/app db"
   [.env] [Line 5] Security Alert: Exposed OpenAI API Key in 'OPENAI_API_KEY'! CRITICAL: Possible live OpenAI API key detected.
```

---

## 6. Step 5: Surgical Remediation

The developer corrects `.env`:
```env
# Corrected: URL encoding space, or wrapping quotes if title
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/app_db"

# Corrected: Kept in local secret manager or replaced with test key
OPENAI_API_KEY=sk-proj-placeholder_key_here
```

Re-running validation:
```bash
python skills/infra/scripts/validate_env.py --env .env --example .env.example
```

**Output:**
```text
🔍 Validating template file: '.env.example'...
🔍 Validating environment file: '.env'...
⚖️ Comparing '.env' against '.env.example'...
----------------------------------------------------------------------
✅ Environment validation COMPLETED SUCCESSFULLY! No syntax or security issues detected.
```

The phase wraps up with the standard handover notice:
> **[NEXT STEP]** *"Environment and dependencies updated successfully! Proceed with the development lifecycle via `/implement` or validate changes using `/test-fix`."*
