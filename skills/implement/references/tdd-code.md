# Operational Guide: TDD Green Phase (`references/tdd-code.md`)

This guide governs the authoring of production code during the TDD Green Phase of `/implement`.

---

## 1. Core Principles of the Green Phase

1. **"Make It Work" Before Optimizing:**
   - Implement the minimal and strictly necessary code required to make the failing tests pass green.
   - Resist the temptation to add speculative features, premature generalizations, or unneeded abstractions.
2. **Strict Static Typing:**
   - Every function, method, parameter, and return value must include comprehensive type annotations.
   - Use `typing.Optional`, `typing.Union`, `typing.List`, `typing.Dict`, or Python 3.10+ union types (`X | None`).
3. **Clean Architecture Boundary Adherence:**
   - Domain entities, value objects, and use cases must depend strictly on abstractions (`Protocol` / `ABC`).
   - Zero imports of infrastructure frameworks (FastAPI, Flask, SQLAlchemy, Django ORM, requests, httpx) within domain and use-case layers.
4. **Single Responsibility at Birth:**
   - Keep classes and methods cohesive from the start. A use case executes a single transaction or business workflow.

---

## 2. Dependency Inversion Pattern (DIP)

Always declare boundaries as abstract protocols and inject dependencies via constructor:

```python
from typing import Protocol, Optional
from dataclasses import dataclass

class IUserRepository(Protocol):
    def find_by_email(self, email: str) -> Optional["User"]:
        ...

    def save(self, user: "User") -> "User":
        ...

class RegisterUserUseCase:
    def __init__(self, repository: IUserRepository) -> None:
        self._repository = repository

    def execute(self, input_dto: RegisterUserInput) -> RegisterUserOutput:
        existing = self._repository.find_by_email(input_dto.email)
        if existing is not None:
            raise UserAlreadyExistsError(f"User with email '{input_dto.email}' already exists.")
        
        user = User.create(email=input_dto.email, name=input_dto.name)
        saved = self._repository.save(user)
        return RegisterUserOutput(user_id=saved.id, status="CREATED")
```

---

## 3. Technical Pivot Protocol

If implementation reveals an SDD contract assumption that is unviable or technically flawed:

1. **Do Not Silently Deviate:** Never alter behavior away from the SDD without formal recording.
2. **Document the Pivot:** Create or append to `02-auditorias/pivots-[slug].md` via `@obsidian`:
   ```markdown
   ---
   type: pivot
   feature: "<slug>"
   date: "<YYYY-MM-DD>"
   ---
   # Technical Pivot: <Title>
   ## Deviation from SDD
   <Explain why the SDD contract or assumption could not be implemented as designed>
   ## Adopted Solution
   <Explain the minimal, type-safe alternative implemented in production code>
   ## Affected Batch
   Batch [N] in task_list.md
   ```
3. **Notify User:** Inform the user in chat regarding the pivot and proceed once acknowledged.

---

## 4. Test Failure Handling & Double-Strike Rule

If running the tests during the Green phase results in an unexpected failure:

1. **Strike 1 (First Failure):**
   - Read the traceback carefully.
   - Formulate the root cause in exactly one sentence.
   - Apply a surgical fix strictly to the production code.
   - Re-run the test suite.
2. **Strike 2 (Second Consecutive Failure):**
   - Re-evaluate assumptions.
   - Apply a second surgical modification without touching test assertions.
   - Re-run the test suite.
3. **Double-Strike Escalation (> 2 Consecutive Failures):**
   - Immediately execute emergency rollback to the last clean checkpoint:
     ```bash
     git reset --hard HEAD
     ```
   - Discard the broken attempt to keep the context window clean.
   - Recommend escalating to `/test-fix` or request user intervention.
