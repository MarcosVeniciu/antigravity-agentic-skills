# Release Readiness Checklist & SemVer Rules

Verification gates, deterministic SemVer logic, and Mode 5 sequence for [`../SKILL.md`](../SKILL.md), [`../resources/release-template.md`](../resources/release-template.md), and [`../scripts/validate_release.py`](../scripts/validate_release.py).

## 1. Living DoD Entry Gate (`01-concepcao/dod-[slug].md`)

| Phase | Scope | Invariant (Zero `- [ ]` Required) |
| :--- | :--- | :--- |
| **1. Conception** | Architecture | BDD scenarios, SDD contracts validated, zero code. |
| **2. Implementation** | Unit TDD | Batches complete, unit tests green, micro-refactor done. |
| **3. Refactoring** | Systemic SOLID | Clean code across `develop...HEAD`, cyclomatic $V(G) \le 10$. |
| **4. Review** | 5-Domain Audit | Architecture, Security, Quality, Performance, Resilience green. |
| **5. Documentation** | Docs & Freeze | Docs/docstrings synced, Mermaid verified, branch frozen. |

---

## 2. Deterministic SemVer 2.0.0 Decision Matrix (`--calculate-semver`)

Computed deterministically via `validate_release.py --calculate-semver develop --current-version v[CURRENT]` ($\text{MAJOR} > \text{MINOR} > \text{PATCH}$ across `git log develop..HEAD`):

| Level | Regex Triggers & Prefixes | Impact & Example |
| :--- | :--- | :--- |
| **MAJOR (`X.0.0`)** | `BREAKING CHANGE:`, `^[a-z]+(\([^)]+\))?!:` (`feat!:`, `fix!:`) | Breaking API/contract change. `v1.4.2 -> v2.0.0`. |
| **MINOR (`X.Y.0`)** | `^feat(\([^)]+\))?:` | Backward-compatible feature. `v1.4.2 -> v1.5.0`. |
| **PATCH (`X.Y.Z`)** | `^(fix\|perf\|refactor\|docs\|chore\|test)(\([^)]+\))?:` | Bugfixes, optimizations. `v1.4.2 -> v1.4.3`. |

---

## 3. Pre-Test Supply-Chain & Fixture Gate + Git Flow Mode 5 Sequence

```bash
python skills/infra/scripts/audit_dependencies.py pyproject.toml
python skills/review/scripts/scan_sinks.py tests/integration/
python -m pytest tests/integration/ -v
python skills/release/scripts/validate_release.py --calculate-semver develop --current-version v[PREV_VERSION]
git add CHANGELOG.md 03-releases/ && git commit -m "chore(release): prepare release v[VERSION]"
git checkout main && git merge --no-ff release/v[VERSION] -m "release: v[VERSION]" && git tag -a v[VERSION] -m "Release v[VERSION]"
git checkout develop && git merge --no-ff release/v[VERSION] -m "merge: sync release v[VERSION] back to develop"
git branch -d release/v[VERSION] feature/[slug]
```
