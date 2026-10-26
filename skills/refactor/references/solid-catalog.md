# Operational Reference: SOLID & Clean Code Refactoring Catalog

This guide provides technical patterns, code smell definitions, and transformation blueprints for systemic macro-refactoring during Phase 3 (`/refactor`).

---

## 1. Clean Code Transformations

### 1.1. Guard Clauses & Inverted Conditionals (Arrow Anti-Pattern)
- **Problem:** Nested `if/else` structures increase cyclomatic complexity ($V(G)$), create deep indentation (the arrow anti-pattern), and force developers to hold complex mental state.
- **Solution:** Invert conditional checks to evaluate error or boundary conditions first, returning or raising exceptions immediately.
- **Code Transformation:**
  ```python
  # BEFORE: Nested logic, V(G) = 6
  def process_payment(account: Account, amount: Decimal) -> PaymentResult:
      if account.is_active:
          if not account.is_frozen:
              if account.balance >= amount:
                  account.deduct(amount)
                  return PaymentResult.SUCCESS
              else:
                  return PaymentResult.INSUFFICIENT_FUNDS
          else:
              return PaymentResult.ACCOUNT_FROZEN
      else:
          return PaymentResult.ACCOUNT_INACTIVE

  # AFTER: Flat guard clauses, V(G) = 4
  def process_payment(account: Account, amount: Decimal) -> PaymentResult:
      if not account.is_active:
          return PaymentResult.ACCOUNT_INACTIVE
      if account.is_frozen:
          return PaymentResult.ACCOUNT_FROZEN
      if account.balance < amount:
          return PaymentResult.INSUFFICIENT_FUNDS

      account.deduct(amount)
      return PaymentResult.SUCCESS
  ```

### 1.2. Extract Function / Method (Single Level of Abstraction)
- **Problem:** Monolithic methods exceeding 20–25 lines mix high-level business orchestration with low-level parsing, calculation, or validation.
- **Solution:** Isolate coherent sub-operations into private helper methods (`_validate_*`, `_compute_*`, `_format_*`), ensuring the main function reads like a high-level summary.
- **Code Transformation:**
  ```python
  # BEFORE: Mixed orchestration and calculation
  def generate_invoice(self, order: Order) -> Invoice:
      # Validation
      if not order.items:
          raise ValueError("Order must contain items")
      # Calculation
      subtotal = Decimal("0.00")
      for item in order.items:
          subtotal += item.price * item.quantity
      discount = Decimal("0.00")
      if subtotal > Decimal("100.00"):
          discount = subtotal * Decimal("0.10")
      tax = (subtotal - discount) * Decimal("0.08")
      total = subtotal - discount + tax
      # Output
      return Invoice(order_id=order.id, subtotal=subtotal, discount=discount, tax=tax, total=total)

  # AFTER: High-level orchestration with extracted helpers
  def generate_invoice(self, order: Order) -> Invoice:
      self._validate_order_has_items(order)
      subtotal = self._calculate_subtotal(order.items)
      discount = self._compute_applicable_discount(subtotal)
      tax = self._calculate_tax(subtotal - discount)
      total = subtotal - discount + tax
      return Invoice(order_id=order.id, subtotal=subtotal, discount=discount, tax=tax, total=total)
  ```

### 1.3. Named Constants & Typed Enums (Magic Values Elimination)
- **Problem:** Hardcoded numbers or string literals (`86400`, `0.15`, `"CONFIRMED"`) lack semantic context and risk inconsistent duplication.
- **Solution:** Promote literals to uppercase module/class constants or `Enum` types.
- **Code Transformation:**
  ```python
  # BEFORE: Magic numbers and strings
  if order.status == "PND" and order.days_pending > 30:
      order.apply_penalty(order.amount * 0.05)

  # AFTER: Named constants and explicit typing
  MAX_PENDING_DAYS_ALLOWED: int = 30
  DEFAULT_PENALTY_RATE: Decimal = Decimal("0.05")

  if order.status == OrderStatus.PENDING and order.days_pending > MAX_PENDING_DAYS_ALLOWED:
      order.apply_penalty(order.amount * DEFAULT_PENALTY_RATE)
  ```

---

## 2. SOLID Principles Across Feature Changesets

### 2.1. Single Responsibility Principle (SRP)
- **Principle:** A module, class, or function should have one, and only one, reason to change.
- **Application on Feature Diff:**
  - Separate business calculation from persistence and serialization.
  - Decompose large classes that manage both entity state and external dispatching into dedicated domain services and infrastructure adapters.

### 2.2. Open/Closed Principle (OCP)
- **Principle:** Software entities should be open for extension, but closed for modification.
- **Application on Feature Diff:**
  - Replace sprawling `if/elif/else` ladders or `match/case` blocks based on type codes with polymorphic dispatch, strategy patterns, or dictionary registries.
  ```python
  # BEFORE: Sprawling type branch (violates OCP)
  def calculate_discount(customer_type: str, amount: Decimal) -> Decimal:
      if customer_type == "regular":
          return amount * Decimal("0.00")
      elif customer_type == "premium":
          return amount * Decimal("0.10")
      elif customer_type == "vip":
          return amount * Decimal("0.20")
      raise ValueError("Unknown customer type")

  # AFTER: Registry / Strategy Pattern (open for extension)
  DISCOUNT_STRATEGIES: Dict[str, Callable[[Decimal], Decimal]] = {
      "regular": lambda amt: Decimal("0.00"),
      "premium": lambda amt: amt * Decimal("0.10"),
      "vip": lambda amt: amt * Decimal("0.20"),
  }

  def calculate_discount(customer_type: str, amount: Decimal) -> Decimal:
      strategy = DISCOUNT_STRATEGIES.get(customer_type)
      if not strategy:
          raise ValueError(f"Unknown customer type: {customer_type}")
      return strategy(amount)
  ```

### 2.3. Liskov Substitution Principle (LSP)
- **Principle:** Subtypes must be substitutable for their base types without breaking client expectations.
- **Application on Feature Diff:**
  - Subclasses must not narrow parameter types or widen return exceptions.
  - Never override a base class method with `raise NotImplementedError("Not supported")`. If a method is unsupported, the class hierarchy is wrong; split the interface.

### 2.4. Interface Segregation Principle (ISP)
- **Principle:** Clients should not be forced to depend on methods they do not use.
- **Application on Feature Diff:**
  - In Python, use lean `typing.Protocol` classes rather than fat abstract base classes.
  ```python
  # Lean, segregated protocols
  from typing import Protocol

  class Reader(Protocol):
      def read(self, entity_id: str) -> Entity: ...

  class Writer(Protocol):
      def save(self, entity: Entity) -> None: ...
  ```

### 2.5. Dependency Inversion Principle (DIP)
- **Principle:** High-level modules should not depend on low-level modules; both should depend on abstractions.
- **Application on Feature Diff:**
  - Eliminate direct instantiation (`self.db = PostgresClient()`) inside use cases or domain services.
  - Require dependencies via constructor arguments typed as abstract protocols or interfaces.
  ```python
  # BEFORE: Direct instantiation (tight coupling)
  class OrderService:
      def __init__(self):
          self.repository = PostgresOrderRepository()
          self.mailer = SmtpEmailNotifier()

  # AFTER: Constructor dependency injection
  class OrderService:
      def __init__(self, repository: OrderRepositoryProtocol, notifier: NotifierProtocol):
          self._repository = repository
          self._notifier = notifier
  ```

---

## 3. AST Complexity Reduction & Algorithmic Heuristics

The scanner [`scripts/ast_complexity.py`](../scripts/ast_complexity.py) calculates McCabe cyclomatic complexity:
$$V(G) = E - N + 2P = 1 + \sum(\text{decision points})$$

### 3.1. How Refactoring Reduces $V(G)$
1. **Guard clauses:** Replace nested branches (`if A: if B:`) with flat sequential guards, eliminating compounding decision branches.
2. **Method extraction:** Each extracted private helper isolates decision points in its own function scope. The parent method's $V(G)$ drops dramatically.
3. **Lookup tables / Polymorphism:** Replacing an 8-branch `if/elif` ladder with a dictionary lookup reduces $V(G)$ from 9 to 1.

### 3.2. Asymptotic Anti-Patterns (Big-O Heuristics)
1. **$O(N^2)$ Nested Loops:**
   - *Problem:* A loop inside a loop over collections scales quadratically.
   - *Remedy:* Index the inner collection in a hash map (`dict`) or `set` prior to the loop ($O(N + M)$).
2. **Linear Search in Loop ($O(N \cdot M)$):**
   - *Problem:* Using `if item in list_of_items:` inside a loop performs a linear scan for every iteration.
   - *Remedy:* Convert `list_of_items` to `set(list_of_items)` before iterating, reducing membership lookups from $O(M)$ to $O(1)$.
