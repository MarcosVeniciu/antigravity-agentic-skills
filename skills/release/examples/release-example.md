# Walkthrough Example: Publishing Release `v1.2.0`

This example illustrates the end-to-end execution of a production release bundle containing two completed features (`feature/auth-jwt` and `feature/rate-limiter`) via [`../SKILL.md`](../SKILL.md).

---

## 1. Scenario Context

- **Target Release Version:** `v1.2.0`
- **Previous Version:** `v1.1.0`
- **Candidate Feature Branches:**
  1. `feature/auth-jwt`: JWT Authentication and RBAC endpoints.
  2. `feature/rate-limiter`: Redis-backed token bucket rate limiting.
- **Git Base Branch:** `develop`

---

## 2. Step-by-Step Execution

### Step 1: Entry Gate Audit & DoD Verification

The release manager inspects the Living DoD files for both features:
```bash
python -c "
from pathlib import Path
for slug in ['auth-jwt', 'rate-limiter']:
    dod = Path(f'01-concepcao/dod-{slug}.md')
    if dod.exists():
        content = dod.read_text(encoding='utf-8')
        unchecked = [line for line in content.splitlines() if '- [ ]' in line]
        print(f'DoD {slug}: {len(unchecked)} unchecked items')
"
```
**Output:**
```text
DoD auth-jwt: 0 unchecked items
DoD rate-limiter: 0 unchecked items
```
Both features achieved 100% DoD completion across Phases 1 through 5.

### Step 2: Release Branch Creation & Integration Verification

```bash
# Checkout latest develop
git checkout develop
git pull origin develop

# Create release branch
git checkout -b release/v1.2.0

# Merge candidate features without fast-forward
git merge --no-ff feature/auth-jwt -m "merge: feature/auth-jwt into release"
git merge --no-ff feature/rate-limiter -m "merge: feature/rate-limiter into release"

# Execute full integration test suite
python -m pytest tests/integration/ -v
```
**Test Results:**
```text
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-8.3.4
collected 14 items

tests/integration/test_auth_integration.py::test_jwt_login_flow PASSED   [  7%]
tests/integration/test_auth_integration.py::test_rbac_forbidden PASSED   [ 14%]
tests/integration/test_rate_limiter.py::test_rate_limit_throttle PASSED  [ 21%]
tests/integration/test_rate_limiter.py::test_rate_limit_recovery PASSED  [ 28%]
...
============================= 14 passed in 2.15s ==============================
```

### Step 3: SemVer Bump & Changelog Generation

Inspecting commits:
- `feat(auth): implement jwt token generation and validation`
- `feat(rate-limit): add redis token bucket middleware`
- `fix(auth): handle expired token edge-case`

Applying [`../references/release-checklist.md`](../references/release-checklist.md):
- Highest precedence commit: `feat:` $\rightarrow$ **MINOR** bump (`v1.1.0` $\rightarrow$ `v1.2.0`).

Populating [`../resources/release-template.md`](../resources/release-template.md) and updating `CHANGELOG.md`:
```markdown
# Changelog

## [v1.2.0] - 2026-10-26

### New Features
- `[feat]`: JWT Authentication and RBAC guard endpoints (ref: `[[sdd-auth-jwt]]`).
- `[feat]`: Redis-backed token bucket rate limiting middleware (ref: `[[sdd-rate-limiter]]`).

### Bug Fixes
- `[fix]`: Correct timestamp parsing for expired JWT tokens.

---
```

### Step 4: Programmatic Validation & Git Flow Finalization

Run the validator script:
```bash
python workflows-skill/release/scripts/validate_release.py \
  --version v1.2.0 \
  --branch release/v1.2.0 \
  --changelog CHANGELOG.md \
  --check-dod "01-concepcao/dod-*.md" \
  --check-clean
```

**Output:**
```text
🚀 Running Release Readiness Validation for version 'v1.2.0'...
✅ [SEMVER OK] Version 'v1.2.0' is valid SemVer 2.0.0.
✅ [BRANCH OK] Branch 'release/v1.2.0' is a valid release branch conforming to conventions.
✅ [CHANGELOG OK] Valid changelog entry found for version 'v1.2.0' in 'CHANGELOG.md'.
✅ [DOD AUDIT OK] All 2 checked DoD file(s) are 100% complete (zero unchecked items).
✅ [GIT STATUS OK] Git working tree is clean.
----------------------------------------------------------------------
🎉 Release validation PASSED for 'v1.2.0'! Ready for Git Flow finalization.
```

Execute Git Flow finalization:
```bash
# Commit release notes
git add CHANGELOG.md 03-releases/
git commit -m "chore(release): prepare release v1.2.0"

# Merge to main and tag
git checkout main
git merge --no-ff release/v1.2.0 -m "release: v1.2.0"
git tag -a v1.2.0 -m "Release v1.2.0"

# Sync develop
git checkout develop
git merge --no-ff release/v1.2.0 -m "merge: sync release v1.2.0 back to develop"

# Branch pruning
git branch -d release/v1.2.0
git branch -d feature/auth-jwt
git branch -d feature/rate-limiter
```

Final system message:
> **[RELEASE COMPLETED]** *"Version `v1.2.0` published successfully with 100% DoD verified, integration tests passed, annotated tag created, and branches merged into `main` and `develop`!"*
