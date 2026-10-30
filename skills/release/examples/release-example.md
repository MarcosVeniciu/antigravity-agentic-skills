# Walkthrough Example: Publishing Release `v1.2.0`

Release trace for `feature/auth-jwt` and `feature/rate-limiter` per [`release-checklist.md`](../references/release-checklist.md) and [`release-template.md`](../resources/release-template.md).

## 1. Parameters & Execution Trace

| Parameter | Value | Parameter | Value |
| :--- | :--- | :--- | :--- |
| **Target Version** | `v1.2.0` (MINOR bump from `v1.1.0`) | **Candidates** | `feature/auth-jwt`, `feature/rate-limiter` |
| **Branches** | `release/v1.2.0` from `develop` -> `main` | **Gate Tool** | [`validate_release.py`](../scripts/validate_release.py) |

| Step | Action | Command & Evidence |
| :--- | :--- | :--- |
| **1. DoD Audit** | Verify `[x]` | `release-auditor` (`EnableWriteTools: false`) scans `01-concepcao/dod-*.md` -> `[PASS]: 100%_DOD_VERIFIED`. |
| **2. Merge & Safe E2E** | Supply-chain & fixture check + E2E | `git merge --no-ff feature/auth-jwt feature/rate-limiter`<br>`python skills/infra/scripts/audit_dependencies.py pyproject.toml`<br>`python skills/review/scripts/scan_sinks.py tests/integration/`<br>`python -m pytest tests/integration/ -v` (14 passed). |
| **3. SemVer Sync** | Deterministic SemVer + Read-Only Draft | `python skills/release/scripts/validate_release.py --calculate-semver develop --current-version v1.1.0` -> `MINOR (v1.2.0)`.<br>`release-auditor` drafts release notes from `<untrusted_commit_log>` per [`release-template.md`](../resources/release-template.md); **Orchestrator** writes `CHANGELOG.md` & `03-releases/changelog-v1.2.0.md`. |
| **4. Finalize** | Git Flow | `python skills/release/scripts/validate_release.py --version v1.2.0 --branch release/v1.2.0 --changelog CHANGELOG.md --check-dod "01-concepcao/dod-*.md" --check-clean` -> PASSED.<br>`git merge --no-ff release/v1.2.0` to `main` & `develop`; tag `v1.2.0`. |
