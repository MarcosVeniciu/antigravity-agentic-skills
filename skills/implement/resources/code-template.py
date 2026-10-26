"""
Pure Production Code Template
Skill: workflows-skill/implement
Path: resources/code-template.py

Demonstrates Clean Architecture, Dependency Inversion (Protocol),
strict static typing, immutable value objects/dataclasses, and custom domain exceptions.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Protocol


# ==============================================================================
# Domain Exceptions
# ==============================================================================

class DomainError(Exception):
    """Base class for all business domain errors."""
    pass


class EntityNotFoundError(DomainError):
    """Raised when a requested domain entity does not exist."""
    pass


class BusinessRuleViolationError(DomainError):
    """Raised when an operation violates an explicit domain invariant."""
    pass


# ==============================================================================
# Domain Entities & Value Objects
# ==============================================================================

@dataclass(frozen=True)
class EntityIdentifier:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Entity identifier cannot be empty.")


@dataclass
class DomainEntity:
    id: EntityIdentifier
    name: str
    balance: Decimal

    def can_debit(self, amount: Decimal) -> bool:
        return self.balance >= amount

    def debit(self, amount: Decimal) -> None:
        if not self.can_debit(amount):
            raise BusinessRuleViolationError("Cannot debit amount: insufficient balance.")
        self.balance -= amount


# ==============================================================================
# Boundary Contracts (Dependency Inversion Principle)
# ==============================================================================

class IDomainRepository(Protocol):
    """Abstract storage boundary protocol."""

    def find_by_id(self, entity_id: EntityIdentifier) -> Optional[DomainEntity]:
        """Retrieve entity by identifier or return None."""
        ...

    def save(self, entity: DomainEntity) -> DomainEntity:
        """Persist entity and return stored instance."""
        ...


# ==============================================================================
# Input / Output Data Transfer Objects (DTOs)
# ==============================================================================

@dataclass(frozen=True)
class ProcessActionInput:
    entity_id: str
    amount: Decimal


@dataclass(frozen=True)
class ProcessActionOutput:
    entity_id: str
    new_balance: Decimal
    status: str


# ==============================================================================
# Use Case / Service Implementation
# ==============================================================================

class ProcessActionUseCase:
    """
    Executes a cohesive business use case.
    Dependencies are injected via constructor adhering to DIP.
    """

    def __init__(self, repository: IDomainRepository) -> None:
        self._repository = repository

    def execute(self, input_dto: ProcessActionInput) -> ProcessActionOutput:
        self._validate_input(input_dto)
        
        entity_id = EntityIdentifier(input_dto.entity_id)
        entity = self._repository.find_by_id(entity_id)
        if entity is None:
            raise EntityNotFoundError(f"Entity '{input_dto.entity_id}' not found.")

        entity.debit(input_dto.amount)
        saved_entity = self._repository.save(entity)

        return ProcessActionOutput(
            entity_id=saved_entity.id.value,
            new_balance=saved_entity.balance,
            status="SUCCESS",
        )

    # --------------------------------------------------------------------------
    # Private Helper Methods (Micro-Refactoring Standards)
    # --------------------------------------------------------------------------

    def _validate_input(self, input_dto: ProcessActionInput) -> None:
        if input_dto.amount <= Decimal("0"):
            raise ValueError("Action amount must be strictly greater than zero.")
