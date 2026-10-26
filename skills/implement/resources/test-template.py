"""
Pure AAA Unit Test Template
Skill: workflows-skill/implement
Path: resources/test-template.py

Demonstrates standard Arrange-Act-Assert (AAA) pattern with isolated boundary mocks,
parametrized edge cases, domain exceptions, concurrency testing, and security assertions.
"""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from typing import Optional, Protocol
from unittest.mock import create_autospec
import pytest


# ==============================================================================
# Domain Interfaces & Entities (Stubbed for template illustration)
# ==============================================================================

class InsufficientFundsError(Exception):
    """Raised when an account balance is insufficient for a transaction."""
    pass


class AccountNotFoundError(Exception):
    """Raised when an account cannot be located in the repository."""
    pass


class IAccountRepository(Protocol):
    """Boundary abstraction for account persistence."""
    def find_by_id(self, account_id: str) -> Optional["AccountStub"]:
        ...

    def update_balance(self, account_id: str, new_balance: Decimal) -> None:
        ...


class AccountStub:
    """Minimal account entity for testing."""
    def __init__(self, account_id: str, balance: Decimal) -> None:
        self.id = account_id
        self.balance = balance


class WithdrawService:
    """Service under test."""
    def __init__(self, repository: IAccountRepository) -> None:
        self._repository = repository

    def execute(self, account_id: str, amount: Decimal) -> Decimal:
        if amount <= Decimal("0"):
            raise ValueError("Withdrawal amount must be strictly positive.")
        account = self._repository.find_by_id(account_id)
        if account is None:
            raise AccountNotFoundError(f"Account '{account_id}' was not found.")
        if account.balance < amount:
            raise InsufficientFundsError(f"Insufficient balance in account '{account_id}'.")
        
        new_balance = account.balance - amount
        self._repository.update_balance(account_id, new_balance)
        account.balance = new_balance
        return new_balance


# ==============================================================================
# Unit Test Suite (AAA Pattern)
# ==============================================================================

def test_should_withdraw_amount_successfully_when_balance_is_sufficient():
    # Arrange
    mock_repo = create_autospec(IAccountRepository, instance=True)
    initial_balance = Decimal("250.00")
    withdraw_amount = Decimal("50.00")
    mock_account = AccountStub(account_id="acc-123", balance=initial_balance)
    mock_repo.find_by_id.return_value = mock_account

    service = WithdrawService(repository=mock_repo)

    # Act
    remaining_balance = service.execute(account_id="acc-123", amount=withdraw_amount)

    # Assert
    assert remaining_balance == Decimal("200.00")
    mock_repo.find_by_id.assert_called_once_with("acc-123")
    mock_repo.update_balance.assert_called_once_with("acc-123", Decimal("200.00"))


@pytest.mark.parametrize(
    "invalid_amount, expected_error_msg",
    [
        (Decimal("0.00"), "Withdrawal amount must be strictly positive."),
        (Decimal("-10.00"), "Withdrawal amount must be strictly positive."),
    ],
)
def test_should_raise_value_error_when_amount_is_non_positive(
    invalid_amount: Decimal, expected_error_msg: str
):
    # Arrange
    mock_repo = create_autospec(IAccountRepository, instance=True)
    service = WithdrawService(repository=mock_repo)

    # Act & Assert
    with pytest.raises(ValueError, match=expected_error_msg):
        service.execute(account_id="acc-123", amount=invalid_amount)


def test_should_raise_insufficient_funds_error_when_balance_is_lower_than_amount():
    # Arrange
    mock_repo = create_autospec(IAccountRepository, instance=True)
    mock_account = AccountStub(account_id="acc-123", balance=Decimal("40.00"))
    mock_repo.find_by_id.return_value = mock_account

    service = WithdrawService(repository=mock_repo)

    # Act & Assert
    with pytest.raises(InsufficientFundsError):
        service.execute(account_id="acc-123", amount=Decimal("100.00"))


def test_should_prevent_double_spend_under_concurrent_race():
    # Arrange: in-memory state tracking to simulate atomic persistence
    class InMemoryAccountRepo:
        def __init__(self, account: AccountStub) -> None:
            self._account = account

        def find_by_id(self, account_id: str) -> Optional[AccountStub]:
            return self._account

        def update_balance(self, account_id: str, new_balance: Decimal) -> None:
            self._account.balance = new_balance

    shared_account = AccountStub(account_id="acc-shared", balance=Decimal("100.00"))
    repo = InMemoryAccountRepo(shared_account)
    service = WithdrawService(repository=repo)

    # Act: 10 parallel threads attempting to withdraw 100 simultaneously
    def try_withdraw():
        try:
            service.execute("acc-shared", Decimal("100.00"))
            return True
        except InsufficientFundsError:
            return False

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(try_withdraw) for _ in range(10)]
        results = [f.result() for f in futures]

    # Assert: Exactly one withdrawal succeeds
    assert results.count(True) == 1
    assert results.count(False) == 9
    assert shared_account.balance == Decimal("0.00")
