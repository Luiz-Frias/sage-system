---
name: Type Safety
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# Python Type Safety Guardrails for Enterprise Insurance Systems

## Overview
Strict type safety is critical for P&C insurance systems where calculation accuracy, data integrity, and regulatory compliance are non-negotiable. This document defines mandatory typing rules and mypy configuration for all Python code.

## Core Principles

### 1. No Implicit Any
- All functions, methods, and variables MUST have explicit type annotations
- `Any` type is forbidden except in documented edge cases with approval
- Dynamic typing patterns must be replaced with proper type unions or generics

### 2. Strict Type Checking
```python
# mypy.ini configuration
[mypy]
python_version = 3.11
strict = True
warn_return_any = True
warn_unused_configs = True
disallow_any_expr = True
disallow_any_decorated = True
disallow_any_explicit = True
disallow_any_generics = True
disallow_subclassing_any = True
disallow_untyped_calls = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
strict_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
```

## Insurance Domain Types

### 1. Monetary Values
```python
from decimal import Decimal
from typing import NewType, Protocol

# Always use Decimal for monetary calculations
Premium = NewType('Premium', Decimal)
Deductible = NewType('Deductible', Decimal)
Coverage = NewType('Coverage', Decimal)
Commission = NewType('Commission', Decimal)

class MonetaryValue(Protocol):
    """Protocol for all monetary calculations in insurance systems"""
    def to_decimal(self) -> Decimal: ...
    def currency_code(self) -> str: ...
    def validate_precision(self) -> bool: ...
```

### 2. Policy Types
```python
from datetime import datetime
from enum import Enum
from typing import Literal, TypedDict, Union

class PolicyStatus(str, Enum):
    QUOTE = "QUOTE"
    BOUND = "BOUND"
    IN_FORCE = "IN_FORCE"
    CANCELLED = "CANCELLED"
    NON_RENEWED = "NON_RENEWED"
    LAPSED = "LAPSED"

class PolicyTerm(TypedDict):
    effective_date: datetime
    expiration_date: datetime
    term_months: Literal[1, 3, 6, 12]

class PolicyIdentifier(TypedDict):
    policy_number: str
    version: int
    company_code: str
    line_of_business: str
```

### 3. Risk Assessment Types
```python
from typing import TypeVar, Generic, Protocol

T = TypeVar('T', bound='RiskFactor')

class RiskFactor(Protocol):
    """Base protocol for all risk factors"""
    def calculate_score(self) -> float: ...
    def get_factor_name(self) -> str: ...
    def validate(self) -> bool: ...

class RiskProfile(Generic[T]):
    """Generic container for risk assessments"""
    factors: list[T]
    base_rate: Decimal
    
    def calculate_premium(self) -> Premium: ...
```

## Function Signature Rules

### 1. Return Type Annotations
```python
# WRONG
def calculate_premium(policy):
    return policy.base_rate * policy.factor

# CORRECT
def calculate_premium(policy: PolicyData) -> Premium:
    """Calculate premium with explicit return type"""
    result: Decimal = policy.base_rate * policy.factor
    return Premium(result.quantize(Decimal('0.01')))
```

### 2. Parameter Types
```python
# WRONG
def apply_discount(premium, discount, reason=None):
    return premium * (1 - discount)

# CORRECT
def apply_discount(
    premium: Premium,
    discount: Decimal,
    reason: str | None = None
) -> tuple[Premium, str]:
    """Apply discount with full type safety"""
    if not 0 <= discount <= 1:
        raise ValueError(f"Invalid discount: {discount}")
    
    new_premium = Premium(premium * (Decimal('1') - discount))
    audit_note = f"Discount applied: {discount:.2%} - {reason or 'No reason provided'}"
    return new_premium, audit_note
```

## Generic Type Patterns

### 1. Repository Pattern
```python
from typing import Protocol, TypeVar, Generic
from abc import abstractmethod

T = TypeVar('T', bound='Entity')

class Entity(Protocol):
    """Base entity protocol"""
    id: str
    created_at: datetime
    updated_at: datetime

class Repository(Generic[T], Protocol):
    """Generic repository protocol for type-safe data access"""
    
    @abstractmethod
    async def find_by_id(self, entity_id: str) -> T | None: ...
    
    @abstractmethod
    async def save(self, entity: T) -> T: ...
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool: ...
```

### 2. Result Types
```python
from typing import TypeVar, Generic, Union

T = TypeVar('T')
E = TypeVar('E', bound=Exception)

class Result(Generic[T, E]):
    """Type-safe result container for operations that may fail"""
    
    def __init__(self, value: T | None = None, error: E | None = None):
        self._value = value
        self._error = error
    
    @property
    def is_success(self) -> bool:
        return self._error is None
    
    def unwrap(self) -> T:
        if self._error:
            raise self._error
        return self._value  # type: ignore
    
    def unwrap_or(self, default: T) -> T:
        return self._value if self.is_success else default
```

## Collection Type Safety

### 1. Typed Collections
```python
from typing import TypedDict, NotRequired

class ClaimData(TypedDict):
    claim_number: str
    policy_number: str
    loss_date: datetime
    reported_date: datetime
    amount: Decimal
    status: Literal["OPEN", "CLOSED", "PENDING"]
    adjustor_notes: NotRequired[list[str]]

# Use specific collection types
ValidatedClaims = NewType('ValidatedClaims', list[ClaimData])
ClaimsByPolicy = NewType('ClaimsByPolicy', dict[str, list[ClaimData]])
```

### 2. Immutable Data Structures
```python
from dataclasses import dataclass, field
from typing import FrozenSet

@dataclass(frozen=True)
class RatingFactors:
    """Immutable rating factors for thread safety"""
    territory_code: str
    protection_class: int
    construction_type: str
    occupancy_type: str
    modifiers: FrozenSet[str] = field(default_factory=frozenset)
```

## Type Guards and Narrowing

### 1. Custom Type Guards
```python
from typing import TypeGuard

def is_valid_policy_number(value: str) -> TypeGuard[PolicyNumber]:
    """Type guard for policy number validation"""
    return bool(re.match(r'^[A-Z]{2}\d{8}$', value))

def is_monetary_value(value: Any) -> TypeGuard[Decimal]:
    """Type guard for monetary values"""
    if isinstance(value, Decimal):
        return value.as_tuple().exponent >= -2
    return False
```

### 2. Exhaustive Pattern Matching
```python
from typing import NoReturn

def process_policy_status(status: PolicyStatus) -> str:
    """Exhaustive pattern matching with type safety"""
    match status:
        case PolicyStatus.QUOTE:
            return "Quote pending"
        case PolicyStatus.BOUND:
            return "Policy bound"
        case PolicyStatus.IN_FORCE:
            return "Policy active"
        case PolicyStatus.CANCELLED:
            return "Policy cancelled"
        case PolicyStatus.NON_RENEWED:
            return "Policy non-renewed"
        case PolicyStatus.LAPSED:
            return "Policy lapsed"
        case _:
            assert_never(status)

def assert_never(value: NoReturn) -> NoReturn:
    """Helper for exhaustive checking"""
    raise AssertionError(f"Unhandled value: {value}")
```

## Integration with Third-Party Libraries

### 1. Type Stubs
```python
# Create type stubs for untyped insurance libraries
# File: stubs/legacy_rating_engine.pyi

from decimal import Decimal
from typing import TypedDict

class RatingRequest(TypedDict):
    zip_code: str
    coverage_amount: Decimal
    deductible: Decimal

def calculate_rate(request: RatingRequest) -> Decimal: ...
```

### 2. Runtime Type Checking
```python
from typeguard import typechecked

@typechecked
def calculate_commission(
    premium: Premium,
    rate: Decimal,
    agent_id: str
) -> Commission:
    """Runtime type validation for critical calculations"""
    if rate < 0 or rate > Decimal('0.5'):
        raise ValueError(f"Invalid commission rate: {rate}")
    
    return Commission(premium * rate)
```

## Gradual Type Migration

### 1. Migration Strategy
```python
# Phase 1: Add basic annotations
def calculate_tax(amount):  # type: (Decimal) -> Decimal
    return amount * Decimal('0.08')

# Phase 2: Modern annotations
def calculate_tax(amount: Decimal) -> Decimal:
    return amount * Decimal('0.08')

# Phase 3: Full type safety
def calculate_tax(
    amount: Premium | Decimal,
    tax_rate: Decimal = Decimal('0.08'),
    jurisdiction: str = "DEFAULT"
) -> tuple[Decimal, str]:
    """Calculate tax with full type safety and audit trail"""
    tax = amount * tax_rate
    audit = f"Tax calculated for {jurisdiction}: {tax}"
    return tax.quantize(Decimal('0.01')), audit
```

## Type Safety Validation

### 1. Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        args: [--strict, --ignore-missing-imports]
        additional_dependencies: [types-all]
```

### 2. CI/CD Integration
```yaml
# GitHub Actions workflow
name: Type Check
on: [push, pull_request]

jobs:
  mypy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install mypy types-all
      - run: mypy . --strict
```

## Performance Considerations

### 1. Type Annotation Performance
- Type annotations have zero runtime overhead
- Use `from __future__ import annotations` for forward references
- Prefer `TypedDict` over dictionaries for better performance

### 2. Runtime Type Checking
- Enable runtime checking only in development/testing
- Use environment variables to disable in production
- Consider `beartype` for fast runtime checking when needed

## Compliance and Audit

### 1. Type Documentation
```python
def calculate_reserve(
    claims: list[ClaimData],
    reserve_factor: Decimal
) -> Decimal:
    """
    Calculate IBNR reserve for insurance compliance.
    
    Args:
        claims: List of validated claim data
        reserve_factor: Reserve factor (must be between 0.1 and 0.5)
    
    Returns:
        Decimal: Calculated reserve amount rounded to nearest cent
    
    Compliance:
        - SOX: Ensures calculation traceability
        - NAIC: Meets reserve calculation standards
    """
    ...
```

### 2. Type Audit Trail
```python
from typing import TypeVar, Protocol
from datetime import datetime

T = TypeVar('T')

class Auditable(Protocol[T]):
    """Protocol for auditable type changes"""
    
    def get_current_value(self) -> T: ...
    def get_previous_value(self) -> T | None: ...
    def get_change_timestamp(self) -> datetime: ...
    def get_change_user(self) -> str: ...
    def get_change_reason(self) -> str: ...
```