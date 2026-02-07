---
name: Dataclasses
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# Python Dataclasses for Insurance Domain Models

## Overview

Python dataclasses provide a clean, efficient way to create classes that primarily store data. For insurance domain models, they offer automatic generation of special methods, type hints support, and optional immutability through frozen classes.

## Basic Dataclass Structure

```python
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict
from enum import Enum

class PolicyStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

@dataclass
class Policy:
    """Insurance policy domain model."""
    policy_number: str
    holder_id: str
    product_code: str
    effective_date: date
    expiry_date: date
    premium_amount: Decimal
    status: PolicyStatus = PolicyStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, any] = field(default_factory=dict)
```

## Frozen Dataclasses for Immutability

```python
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import date
from typing import Tuple

@dataclass(frozen=True)
class RiskProfile:
    """Immutable risk profile for underwriting."""
    profile_id: str
    risk_score: float
    risk_factors: Tuple[str, ...]  # Use tuple for immutable sequences
    assessment_date: date
    
    def with_updated_score(self, new_score: float) -> 'RiskProfile':
        """Create new instance with updated score (immutability pattern)."""
        return RiskProfile(
            profile_id=self.profile_id,
            risk_score=new_score,
            risk_factors=self.risk_factors,
            assessment_date=date.today()
        )

@dataclass(frozen=True)
class Premium:
    """Immutable premium calculation result."""
    base_amount: Decimal
    taxes: Decimal
    fees: Decimal
    discounts: Decimal = Decimal('0.00')
    
    @property
    def total_amount(self) -> Decimal:
        """Calculate total premium amount."""
        return self.base_amount + self.taxes + self.fees - self.discounts
```

## Field Validation with Validators

```python
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
import re

def validate_policy_number(policy_number: str) -> str:
    """Validate policy number format."""
    pattern = r'^POL-\d{4}-\d{6}$'
    if not re.match(pattern, policy_number):
        raise ValueError(f"Invalid policy number format: {policy_number}")
    return policy_number

def validate_amount(amount: Decimal) -> Decimal:
    """Validate monetary amount."""
    if amount < 0:
        raise ValueError(f"Amount cannot be negative: {amount}")
    if amount.as_tuple().exponent < -2:
        raise ValueError(f"Amount cannot have more than 2 decimal places: {amount}")
    return amount

@dataclass
class Claim:
    """Insurance claim with validation."""
    claim_id: str
    policy_number: str
    claim_date: date
    incident_date: date
    claim_amount: Decimal
    description: str
    status: str = "submitted"
    documents: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate fields after initialization."""
        # Validate policy number
        self.policy_number = validate_policy_number(self.policy_number)
        
        # Validate claim amount
        self.claim_amount = validate_amount(self.claim_amount)
        
        # Validate dates
        if self.incident_date > self.claim_date:
            raise ValueError("Incident date cannot be after claim date")
        
        # Validate status
        valid_statuses = {"submitted", "processing", "approved", "rejected", "paid"}
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}")

@dataclass
class PolicyHolder:
    """Policy holder with comprehensive validation."""
    holder_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    
    def __post_init__(self):
        """Validate and normalize fields."""
        # Email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError(f"Invalid email: {self.email}")
        
        # Phone validation and normalization
        if self.phone:
            # Remove non-digits
            digits = re.sub(r'\D', '', self.phone)
            if len(digits) not in [10, 11]:  # US phone numbers
                raise ValueError(f"Invalid phone number: {self.phone}")
            self.phone = digits
        
        # Age validation
        if self.date_of_birth:
            age = (date.today() - self.date_of_birth).days // 365
            if age < 18:
                raise ValueError("Policy holder must be 18 or older")
```

## Post-init Processing

```python
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict
import uuid

@dataclass
class Quote:
    """Insurance quote with automatic calculations."""
    product_code: str
    base_premium: Decimal
    risk_multiplier: float = 1.0
    discounts: List[Dict[str, Decimal]] = field(default_factory=list)
    fees: List[Dict[str, Decimal]] = field(default_factory=list)
    
    # Auto-generated fields
    quote_id: str = field(init=False)
    created_at: datetime = field(init=False)
    total_premium: Decimal = field(init=False)
    total_discount: Decimal = field(init=False)
    total_fees: Decimal = field(init=False)
    
    def __post_init__(self):
        """Calculate derived fields."""
        # Generate quote ID
        self.quote_id = f"QTE-{uuid.uuid4().hex[:8].upper()}"
        self.created_at = datetime.now()
        
        # Calculate totals
        self.total_discount = sum(d['amount'] for d in self.discounts)
        self.total_fees = sum(f['amount'] for f in self.fees)
        
        # Calculate final premium
        adjusted_base = self.base_premium * Decimal(str(self.risk_multiplier))
        self.total_premium = adjusted_base - self.total_discount + self.total_fees

@dataclass
class PolicyDocument:
    """Document with automatic metadata extraction."""
    document_id: str
    document_type: str
    file_path: str
    uploaded_by: str
    
    # Auto-calculated fields
    file_size: Optional[int] = field(init=False, default=None)
    mime_type: Optional[str] = field(init=False, default=None)
    uploaded_at: datetime = field(init=False)
    
    def __post_init__(self):
        """Extract file metadata."""
        import os
        import mimetypes
        
        self.uploaded_at = datetime.now()
        
        if os.path.exists(self.file_path):
            self.file_size = os.path.getsize(self.file_path)
            self.mime_type = mimetypes.guess_type(self.file_path)[0]
```

## Inheritance Patterns

```python
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from abc import ABC, abstractmethod

@dataclass
class BaseEntity(ABC):
    """Base class for all domain entities."""
    id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def update_timestamp(self):
        """Update the modification timestamp."""
        self.updated_at = datetime.now()
        self.version += 1

@dataclass
class InsuranceProduct(BaseEntity):
    """Base insurance product."""
    product_code: str
    product_name: str
    category: str
    is_active: bool = True
    min_coverage: Decimal = Decimal('0.00')
    max_coverage: Decimal = Decimal('1000000.00')

@dataclass
class LifeInsuranceProduct(InsuranceProduct):
    """Life insurance specific product."""
    min_age: int = 18
    max_age: int = 65
    medical_exam_required: bool = True
    beneficiary_required: bool = True
    
    def __post_init__(self):
        """Set life insurance defaults."""
        self.category = "life"
        if self.min_age >= self.max_age:
            raise ValueError("Min age must be less than max age")

@dataclass
class AutoInsuranceProduct(InsuranceProduct):
    """Auto insurance specific product."""
    vehicle_types: List[str] = field(default_factory=list)
    coverage_types: List[str] = field(default_factory=list)
    deductible_options: List[Decimal] = field(default_factory=list)
    
    def __post_init__(self):
        """Set auto insurance defaults."""
        self.category = "auto"
        if not self.coverage_types:
            self.coverage_types = ["liability", "collision", "comprehensive"]

# Composition pattern
@dataclass
class Coverage:
    """Insurance coverage component."""
    coverage_type: str
    coverage_amount: Decimal
    deductible: Decimal = Decimal('0.00')
    
@dataclass
class PolicyWithCoverage:
    """Policy composed with coverage details."""
    policy: Policy
    coverages: List[Coverage] = field(default_factory=list)
    
    @property
    def total_coverage(self) -> Decimal:
        """Calculate total coverage amount."""
        return sum(c.coverage_amount for c in self.coverages)
```

## Serialization/Deserialization

```python
from dataclasses import dataclass, field, asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any, Type, TypeVar
import json

T = TypeVar('T')

class EnhancedJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles special types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        elif is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)

@dataclass
class SerializablePolicy:
    """Policy with serialization support."""
    policy_number: str
    holder_id: str
    effective_date: date
    premium: Decimal
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), cls=EnhancedJSONEncoder)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with type conversions."""
        data = asdict(self)
        # Convert special types
        data['effective_date'] = self.effective_date.isoformat()
        data['premium'] = str(self.premium)
        return data
    
    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create instance from dictionary."""
        # Convert string dates back to date objects
        if 'effective_date' in data:
            data['effective_date'] = date.fromisoformat(data['effective_date'])
        # Convert string decimals back to Decimal
        if 'premium' in data:
            data['premium'] = Decimal(data['premium'])
        return cls(**data)

# Advanced serialization with nested dataclasses
@dataclass
class Address:
    """Address component."""
    street: str
    city: str
    state: str
    zip_code: str
    
@dataclass
class InsuredEntity:
    """Entity being insured."""
    entity_id: str
    entity_type: str
    name: str
    address: Address
    valuation: Decimal
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InsuredEntity':
        """Deserialize with nested objects."""
        if 'address' in data and isinstance(data['address'], dict):
            data['address'] = Address(**data['address'])
        if 'valuation' in data:
            data['valuation'] = Decimal(str(data['valuation']))
        return cls(**data)
```

## Performance Considerations

```python
from dataclasses import dataclass, field
from functools import cached_property
from typing import List, Dict, Set
import sys

# Use slots for memory efficiency
@dataclass
class EfficientClaim:
    """Memory-efficient claim using slots."""
    __slots__ = ['claim_id', 'policy_number', 'amount', 'status', '_cache']
    
    claim_id: str
    policy_number: str
    amount: Decimal
    status: str
    
    def __post_init__(self):
        self._cache = {}

# Lazy evaluation for expensive computations
@dataclass
class RiskAssessment:
    """Risk assessment with lazy evaluation."""
    assessment_id: str
    data_points: List[Dict[str, float]]
    
    @cached_property
    def risk_score(self) -> float:
        """Calculate risk score only when accessed."""
        # Expensive calculation
        total_weight = sum(dp['weight'] for dp in self.data_points)
        weighted_sum = sum(
            dp['value'] * dp['weight'] 
            for dp in self.data_points
        )
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    @cached_property
    def risk_category(self) -> str:
        """Determine risk category based on score."""
        score = self.risk_score
        if score < 0.3:
            return "low"
        elif score < 0.7:
            return "medium"
        else:
            return "high"

# Comparison of memory usage
def compare_memory_usage():
    """Compare memory usage of different approaches."""
    # Regular dataclass
    @dataclass
    class RegularPolicy:
        policy_id: str
        amount: Decimal
        status: str
    
    # Slotted dataclass
    @dataclass
    class SlottedPolicy:
        __slots__ = ['policy_id', 'amount', 'status']
        policy_id: str
        amount: Decimal
        status: str
    
    regular = RegularPolicy("P001", Decimal("1000.00"), "active")
    slotted = SlottedPolicy("P001", Decimal("1000.00"), "active")
    
    print(f"Regular size: {sys.getsizeof(regular.__dict__)}")
    print(f"Slotted size: {sys.getsizeof(slotted)}")
```

## Integration with Pydantic

```python
from dataclasses import dataclass
from pydantic import BaseModel, validator, Field
from pydantic.dataclasses import dataclass as pydantic_dataclass
from datetime import date
from decimal import Decimal
from typing import Optional, List

# Pure Pydantic model
class PydanticPolicy(BaseModel):
    """Pydantic model with validation."""
    policy_number: str = Field(..., regex=r'^POL-\d{4}-\d{6}$')
    holder_id: str
    premium: Decimal = Field(..., gt=0, decimal_places=2)
    effective_date: date
    
    @validator('effective_date')
    def validate_effective_date(cls, v):
        if v < date.today():
            raise ValueError('Effective date cannot be in the past')
        return v
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat()
        }

# Pydantic dataclass (hybrid approach)
@pydantic_dataclass
class HybridClaim:
    """Dataclass with Pydantic validation."""
    claim_id: str
    policy_number: str = Field(..., regex=r'^POL-\d{4}-\d{6}$')
    claim_amount: Decimal = Field(..., gt=0)
    incident_date: date
    claim_date: date = Field(default_factory=date.today)
    
    def __post_init__(self):
        """Additional validation."""
        if self.incident_date > self.claim_date:
            raise ValueError("Incident date cannot be after claim date")

# Converting between formats
@dataclass
class StandardDataclass:
    """Standard dataclass."""
    field1: str
    field2: int
    
def dataclass_to_pydantic(dc_instance) -> BaseModel:
    """Convert dataclass to Pydantic model."""
    class DynamicModel(BaseModel):
        field1: str
        field2: int
    
    return DynamicModel(**asdict(dc_instance))
```

## Complete Example: Insurance Policy System

```python
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Set
from enum import Enum
import json
import uuid

# Enums
class PolicyStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class ClaimStatus(Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"

# Value objects (frozen)
@dataclass(frozen=True)
class Money:
    """Immutable money value object."""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

@dataclass(frozen=True)
class Period:
    """Insurance coverage period."""
    start_date: date
    end_date: date
    
    def __post_init__(self):
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
    
    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days
    
    def contains(self, check_date: date) -> bool:
        return self.start_date <= check_date <= self.end_date

# Domain entities
@dataclass
class Coverage:
    """Insurance coverage details."""
    coverage_type: str
    coverage_limit: Money
    deductible: Money
    included_perils: Set[str] = field(default_factory=set)
    excluded_perils: Set[str] = field(default_factory=set)

@dataclass
class PolicyHolder:
    """Insurance policy holder."""
    holder_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: date
    address: Dict[str, str] = field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> int:
        today = date.today()
        return (today - self.date_of_birth).days // 365

@dataclass
class Policy:
    """Comprehensive insurance policy."""
    policy_number: str = field(default_factory=lambda: f"POL-{date.today().year}-{uuid.uuid4().hex[:6].upper()}")
    holder: PolicyHolder
    product_code: str
    coverages: List[Coverage]
    premium: Money
    period: Period
    status: PolicyStatus = PolicyStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate policy consistency."""
        if not self.coverages:
            raise ValueError("Policy must have at least one coverage")
        
        # Validate all money values have same currency
        currency = self.premium.currency
        for coverage in self.coverages:
            if coverage.coverage_limit.currency != currency:
                raise ValueError("All amounts must be in same currency")
    
    @property
    def is_active(self) -> bool:
        return (self.status == PolicyStatus.ACTIVE and 
                self.period.contains(date.today()))
    
    @property
    def total_coverage_limit(self) -> Money:
        """Calculate total coverage across all coverages."""
        total = self.coverages[0].coverage_limit
        for coverage in self.coverages[1:]:
            total = total.add(coverage.coverage_limit)
        return total
    
    def activate(self) -> None:
        """Activate the policy."""
        if self.status != PolicyStatus.DRAFT:
            raise ValueError(f"Cannot activate policy in {self.status} status")
        self.status = PolicyStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def suspend(self, reason: str) -> None:
        """Suspend the policy."""
        if self.status != PolicyStatus.ACTIVE:
            raise ValueError(f"Cannot suspend policy in {self.status} status")
        self.status = PolicyStatus.SUSPENDED
        self.metadata['suspension_reason'] = reason
        self.metadata['suspended_at'] = datetime.now().isoformat()
        self.updated_at = datetime.now()

@dataclass
class Claim:
    """Insurance claim."""
    claim_id: str = field(default_factory=lambda: f"CLM-{uuid.uuid4().hex[:8].upper()}")
    policy: Policy
    incident_date: date
    reported_date: date = field(default_factory=date.today)
    claim_amount: Money
    description: str
    status: ClaimStatus = ClaimStatus.SUBMITTED
    documents: List[str] = field(default_factory=list)
    adjuster_notes: List[Dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate claim."""
        if not self.policy.is_active:
            raise ValueError("Cannot create claim for inactive policy")
        
        if not self.policy.period.contains(self.incident_date):
            raise ValueError("Incident date must be within policy period")
        
        if self.incident_date > self.reported_date:
            raise ValueError("Incident date cannot be after reported date")
        
        if self.claim_amount.currency != self.policy.premium.currency:
            raise ValueError("Claim amount currency must match policy currency")
    
    def add_document(self, document_path: str) -> None:
        """Add document to claim."""
        self.documents.append(document_path)
        self.updated_at = datetime.now()
    
    def add_adjuster_note(self, note: str, adjuster_id: str) -> None:
        """Add adjuster note to claim."""
        self.adjuster_notes.append({
            'note': note,
            'adjuster_id': adjuster_id,
            'timestamp': datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def approve(self, approved_amount: Money, approver_id: str) -> None:
        """Approve the claim."""
        if self.status != ClaimStatus.UNDER_REVIEW:
            raise ValueError(f"Cannot approve claim in {self.status} status")
        
        self.status = ClaimStatus.APPROVED
        self.metadata['approved_amount'] = str(approved_amount.amount)
        self.metadata['approved_by'] = approver_id
        self.metadata['approved_at'] = datetime.now().isoformat()
        self.updated_at = datetime.now()

# Usage example
if __name__ == "__main__":
    # Create policy holder
    holder = PolicyHolder(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="555-0123",
        date_of_birth=date(1980, 1, 1),
        address={
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345"
        }
    )
    
    # Create coverages
    liability_coverage = Coverage(
        coverage_type="liability",
        coverage_limit=Money(Decimal("100000.00")),
        deductible=Money(Decimal("1000.00")),
        included_perils={"collision", "theft", "vandalism"}
    )
    
    # Create policy
    policy = Policy(
        holder=holder,
        product_code="AUTO-FULL",
        coverages=[liability_coverage],
        premium=Money(Decimal("1200.00")),
        period=Period(date.today(), date(2024, 12, 31))
    )
    
    # Activate policy
    policy.activate()
    
    # Create claim
    claim = Claim(
        policy=policy,
        incident_date=date.today(),
        claim_amount=Money(Decimal("5000.00")),
        description="Rear-end collision at intersection"
    )
    
    print(f"Policy: {policy.policy_number}")
    print(f"Status: {policy.status.value}")
    print(f"Claim: {claim.claim_id}")
    print(f"Claim Status: {claim.status.value}")
```

## Best Practices

1. **Use Frozen Dataclasses for Value Objects**: Make immutable objects frozen to prevent accidental modification
2. **Validate in __post_init__**: Perform complex validation after initialization
3. **Use Type Hints**: Always specify types for better IDE support and documentation
4. **Prefer Composition**: Use composition over inheritance for flexibility
5. **Lazy Evaluation**: Use @cached_property for expensive computations
6. **Consistent Naming**: Follow Python naming conventions (snake_case)
7. **Document Domain Rules**: Include docstrings explaining business logic
8. **Handle Edge Cases**: Validate all inputs and handle edge cases explicitly
9. **Use Enums**: Replace string constants with Enums for type safety
10. **Consider Performance**: Use __slots__ for frequently created objects