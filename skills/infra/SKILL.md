---
name: infra
description: Orchestrates environment diagnostics, package manifest maintenance, container configuration validation, and strict secret containment.
---

# Skill: Infrastructure Governance (`/infra`)

| Invariant | Operational Rule |
| :--- | :--- |
| **Zero Domain Edits** | Confine changes to manifests and `.env*`. Zero edits in `src/`. |
| **Zero Blind Upgrades** | Pin explicit versions (`poetry add`, `npm install --save-exact`). |
| **Zero Leaked Secrets** | Never commit `.env`. Maintain placeholders per [`env-template.md`](./resources/env-template.md). |

---

## Execution Pipeline

| Step | Directive | CLI / Refs |
| :--- | :--- | :--- |
| **1. Discover** | Scan manifests and conventions. | [`infra-setup.md`](./references/infra-setup.md) |
| **2. Configure** | Apply pinned manifests, multi-stage Dockerfiles. | [`infra-setup.md`](./references/infra-setup.md) |
| **3. Sync** | Sync `.env.example` per [`env-template.md`](./resources/env-template.md). | [`infra-setup.md`](./references/infra-setup.md) |
| **4. Validate** | Enforce syntax and secret audits. Ref: [`infra-example.md`](./examples/infra-example.md). | [`validate_env.py`](./scripts/validate_env.py) |

```bash
python skills/infra/scripts/validate_env.py .env.example
python skills/infra/scripts/validate_env.py --env .env --example .env.example --strict
```
