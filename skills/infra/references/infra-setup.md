# Infrastructure Setup, Supply-Chain Audit & Security Hygiene

Specifications per [`../SKILL.md`](../SKILL.md), [`../resources/env-template.md`](../resources/env-template.md), [`../scripts/audit_dependencies.py`](../scripts/audit_dependencies.py), and [`../scripts/validate_env.py`](../scripts/validate_env.py).

## 1. Environment & Container Architecture

| Domain | Invariant | Enforcement / Syntax |
| :--- | :--- | :--- |
| **`.env`** | Local dev only; strictly in `.gitignore`. | Never commit to VCS. Prohibit live secrets. |
| **`.env.example`** | SSOT template for required variables. | Checked into VCS; safe placeholders only. |
| **Containers** | Multi-stage build; non-root user; immutable tags. | `USER appuser`, pin `python:3.11-slim`, zero secrets. |
| **`.dockerignore`** | Context isolation. | Exclude `.git/`, `.env`, `node_modules/`, `__pycache__/`, `.venv/`, `.dart_tool/`. |

---

## 2. Multi-Ecosystem Dependency Management & Anti-Slopsquatting

Before installing any package or modifying a manifest, run [`audit_dependencies.py`](../scripts/audit_dependencies.py) to prevent **Slopsquatting** (hallucinated or typosquatted packages registered by attackers).

| Ecosystem | Manifest & Lockfile | Registry API Checked by `audit_dependencies.py` | Pinning & Native Audit CLI |
| :--- | :--- | :--- | :--- |
| **Python** | `pyproject.toml`, `requirements.txt`, `poetry.lock` | `https://pypi.org/pypi/{pkg}/json` | `poetry add <pkg>`; `pip-audit` |
| **Node / TS** | `package.json`, `package-lock.json` | `https://registry.npmjs.org/{pkg}` | `npm i --save-exact <pkg>`; `npm audit` |
| **Dart / Flutter** | `pubspec.yaml`, `pubspec.lock` | `https://pub.dev/api/packages/{pkg}` | `flutter pub add <pkg>`; `dart pub outdated` |
| **Rust** | `Cargo.toml`, `Cargo.lock` | `https://crates.io/api/v1/crates/{pkg}` | `cargo add <pkg>`; `cargo audit` |
| **Go** | `go.mod`, `go.sum` | `https://proxy.golang.org/{pkg}/@latest` | `go get <pkg>@vX.Y.Z`; `govulncheck` |
| **.NET (C#)** | `*.csproj`, `packages.lock.json` | `https://api.nuget.org/v3-flatcontainer/{pkg}/index.json` | `dotnet add package <pkg> --version X.Y.Z` |
| **PHP** | `composer.json`, `composer.lock` | `https://repo.packagist.org/p2/{vendor}/{pkg}.json` | `composer require <vendor>/<pkg>:^X.Y` |

### Anti-Slopsquatting & Import Parity Rules
1. **Existence & Version Gate:** Reject any package or pinned version returning HTTP 404 from its canonical registry.
2. **Lineage & Age Gate (`--min-age-days 60`):** Packages published `< 60` days ago, with only `1` release, or lacking a verifiable repository URL (`github.com`, `gitlab.com`, `bitbucket.org`) trigger `[SLOPSQUATTING_RISK]` and `[NEEDS_WEB_AUDIT]`.
3. **Subagent Web Escalation (`dependency-auditor`):** When `[NEEDS_WEB_AUDIT]` fires or the manifest belongs to an unlisted ecosystem (e.g., Maven/Gradle, Swift, Elixir), define and invoke `dependency-auditor` (`Model: "flash"`, `EnableWriteTools: false`, tool: `search_web`) to verify the official docs, authentic package slug, and submodule API existence.
4. **Source Import Parity (`--scan-imports <dir>`):** Cross-check actual imports in source files (`import x` in Python AST, `import/require` in Node, `import 'package:x/...'` in Dart/Flutter) against declared manifest dependencies to catch hallucinated modules or missing declarations.

---

## 3. Secret Patterns ([`validate_env.py`](../scripts/validate_env.py))

| Token Category | Regex Pattern | Severity |
| :--- | :--- | :--- |
| **AWS Key** | `AKIA[0-9A-Z]{16}` | CRITICAL |
| **JWT Token** | `eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}` | CRITICAL |
| **OpenAI Key** | `sk-[a-zA-Z0-9]{32,}` \| `sk-proj-[a-zA-Z0-9_-]{32,}` | CRITICAL |
| **Private Key** | `-----BEGIN[ A-Z_-]*PRIVATE KEY` | CRITICAL |
| **GitHub Token** | `gh[pousr]_[A-Za-z0-9_]{36,}` \| `github_pat_[A-Za-z0-9_]{40,}` | CRITICAL |
