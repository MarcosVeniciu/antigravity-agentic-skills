# TDD Green Phase Specification (`references/tdd-code.md`)

## 1. Production Code Invariants

| Rule | Requirement |
| :--- | :--- |
| **YAGNI** | Pass batch tests and satisfy mapped SDD contracts. |
| **Typing** | 100% typed (`Protocol`, `dataclass(frozen=True)`, `X | None`). |
| **Clean Arch** | Constructor injection. Zero infra in domain. Ref: [`code-template.py`](../resources/code-template.py). |
| **SRP** | Single workflow per use case; methods <= 25 lines. |

## 2. Dependency Inversion Pattern (DIP)

```python
from typing import Protocol, Optional
class IUserRepository(Protocol):
    def find_by_email(self, email: str) -> Optional["User"]: ...
    def save(self, user: "User") -> "User": ...
class RegisterUserUseCase:
    def __init__(self, repo: IUserRepository) -> None: self._repo = repo
```

## 3. Technical Pivot & Double-Strike Protocol

| Rule | Directive |
| :--- | :--- |
| **SDD Pivot** | Log in `02-auditorias/pivots-[slug].md` via `@obsidian` (`type: pivot`, `Deviation`, `Solution`, or YAML `pivots:` list). Pass `--pivots` to `check_sdd_drift.py`. |
| **Anti-Slopsquatting** | Import ONLY Python stdlib or packages explicitly declared in the project manifest (`pyproject.toml` / `requirements.txt`). |
| **Strikes** | Strike 1: root cause in 1 sentence, fix `src/`. Strike 2: 2nd fix. > 2: run `git stash push -u -m "antigravity-safety-rollback-strike2"` then `git reset --hard HEAD` (or `git checkout -- <batch_files>`); escalate. |