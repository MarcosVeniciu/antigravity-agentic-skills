# Environment Configuration Template (`.env.example`)

Use the template below when creating or synchronizing `.env.example` across services.

---

```env
# ==============================================================================
# General Application Settings
# ==============================================================================
# Execution environment: development | staging | production
APP_ENV=development
# Debug mode flag: true | false
APP_DEBUG=true
# Port on which the HTTP service will listen
PORT=3000
# Base public URL of the application
APP_URL=http://localhost:3000
# Logging verbosity level: DEBUG | INFO | WARNING | ERROR
LOG_LEVEL=INFO

# ==============================================================================
# Database & Cache Configurations
# ==============================================================================
# Primary relational database connection URL (PostgreSQL / MySQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app_db
# Connection pool size
DB_POOL_SIZE=10
# Redis cache host and port
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
# Redis password (leave empty for local dev)
REDIS_PASSWORD=""

# ==============================================================================
# Authentication & Security
# ==============================================================================
# Secret key for JWT signature (generate minimum 32 chars in production)
JWT_SECRET=your-super-secret-jwt-key-minimum-32-chars
# Token expiration duration (e.g., 15m, 1h, 7d)
JWT_EXPIRES_IN=1h
# Secret key for session cookies
SESSION_SECRET=session-cookie-secret-key-placeholder

# ==============================================================================
# External Integrations & APIs
# ==============================================================================
# OpenAI API key (replace with your key in local .env)
OPENAI_API_KEY=sk-proj-placeholder_key_here
# Webhook notification callback endpoint
WEBHOOK_URL=https://api.example.com/v1/webhook
# Object storage bucket and endpoint
STORAGE_BUCKET=app-assets-dev
STORAGE_ENDPOINT=http://localhost:9000

# ==============================================================================
# Telemetry & Monitoring
# ==============================================================================
# Sentry DSN for error reporting (leave empty to disable in dev)
SENTRY_DSN=""
# OpenTelemetry OTLP collector endpoint
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

---
*Refer to [`../references/infra-setup.md`](../references/infra-setup.md) for rules and [`../SKILL.md`](../SKILL.md) for execution.*
