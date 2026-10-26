# Reference: Release Readiness Checklist & SemVer 2.0.0 Rules

This document defines the strict operational verification gates, Semantic Versioning (SemVer 2.0.0) calculation rules, and readiness criteria required before publishing an official release via [`../SKILL.md`](../SKILL.md).

---

## 1. 100% Living DoD Entry Gate

A release candidate may only include feature branches that have achieved complete, unconditional DoD sign-off.

### Audit Protocol

For each candidate feature branch `feature/[slug]`:
1. Open and inspect `01-concepcao/dod-[slug].md`.
2. Verify all five mandatory phase gates are marked complete:
   - [x] **Phase 1 (Conception & Architecture):** BDD scenarios defined, SDD contracts validated, zero production code invariant respected.
   - [x] **Phase 2 (Implementation & TDD):** All TDD batches completed, unit tests 100% green, local micro-refactor applied, zero mock leaks in domain.
   - [x] **Phase 3 (Macro-Refactoring):** Clean code and SOLID principles validated across `git diff develop...HEAD`, AST cyclomatic complexity $V(G) \le 10$.
   - [x] **Phase 4 (5-Domain Review):** Architecture, Security OWASP, Quality AST, Performance Big-O, and Resilience audit checklists passed.
   - [x] **Phase 5 (Documentation & Freeze):** Module READMEs updated, Mermaid diagrams verified, in-code docstrings enriched, feature branch frozen.
3. **Rejection Rule:** If any checklist item displays an unchecked box (`- [ ]`), the feature is **strictly disqualified** from the release. The orchestrator must notify the team and exclude the branch until remediation is completed.

---

## 2. Semantic Versioning (SemVer 2.0.0) Decision Matrix

Given a current version `vMAJOR.MINOR.PATCH` (e.g., `v1.4.2`):

```
+--------------------------------------------------------------------------+
|                          SemVer 2.0.0 Matrix                             |
+-------------------+-----------------------------------+------------------+
| Level             | Triggers / Commit Types           | Example Bump     |
+-------------------+-----------------------------------+------------------+
| MAJOR (X.0.0)     | • BREAKING CHANGE footer          | v1.4.2 -> v2.0.0 |
|                   | • feat!: or fix!: breaking prefix |                  |
|                   | • Public API signature change     |                  |
|                   | • Incompatible database schema    |                  |
+-------------------+-----------------------------------+------------------+
| MINOR (X.Y.0)     | • feat: new backward-compatible   | v1.4.2 -> v1.5.0 |
|                   |   feature                         |                  |
|                   | • Additive non-breaking endpoint  |                  |
|                   | • Deprecations (with fallback)    |                  |
+-------------------+-----------------------------------+------------------+
| PATCH (X.Y.Z)     | • fix: backward-compatible bugfix | v1.4.2 -> v1.4.3 |
|                   | • perf: performance optimization  |                  |
|                   | • refactor: structural cleanups   |                  |
|                   | • docs: doc updates               |                  |
|                   | • chore / style: maintenance      |                  |
+-------------------+-----------------------------------+------------------+
```

### Precedence Resolution
If a release bundle contains a combination of commits, the highest precedence level applies:
$$\text{MAJOR} > \text{MINOR} > \text{PATCH}$$

---

## 3. Pre-Release Verification Checklist

Execute and check off each item before merging to `main`:

- [ ] **Working Directory Hygiene:** `git status --porcelain` must be completely empty (no untracked or modified files).
- [ ] **Clean Branch State:** Active branch is `release/v[VERSION]` branching off `develop`.
- [ ] **All Candidate Features Merged:** Features merged with `--no-ff` preserving topological history.
- [ ] **Integration Test Suite Passing:** `python -m pytest tests/integration/ -v` passes with 0 failures and 0 errors.
- [ ] **End-to-End Test Suite Passing:** Any external or smoke test suites pass green against local containerized test environments.
- [ ] **Release Notes Compiled:** Documented in `CHANGELOG.md` using [`../resources/release-template.md`](../resources/release-template.md).
- [ ] **Obsidian Vault Synced:** Copy saved at `03-releases/changelog-v[VERSION].md`.
- [ ] **Programmatic Validation:** Executed [`../scripts/validate_release.py`](../scripts/validate_release.py) with exit code 0.

---

## 4. Git Flow Mode 5 Finalization Sequence

```bash
# 1. Commit release metadata
git add CHANGELOG.md 03-releases/
git commit -m "chore(release): prepare release v[VERSION]"

# 2. Merge to main and tag
git checkout main
git pull origin main
git merge --no-ff release/v[VERSION] -m "release: v[VERSION]"
git tag -a v[VERSION] -m "Release v[VERSION]"

# 3. Synchronize develop
git checkout develop
git pull origin develop
git merge --no-ff release/v[VERSION] -m "merge: sync release v[VERSION] back to develop"

# 4. Clean up local branches
git branch -d release/v[VERSION]
git branch -d feature/[slug-1]
git branch -d feature/[slug-2]
```
