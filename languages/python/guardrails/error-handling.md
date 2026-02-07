---
name: Error Handling
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# Python Error Handling Guardrails for Enterprise Insurance Systems

## Overview
Error handling in P&C insurance systems must ensure data integrity, maintain audit trails, and comply with regulatory requirements. This document defines mandatory error handling patterns and exception propagation strategies.

## Core Principles

### 1. Never Swallow Exceptions
- All exceptions MUST be logged with full context
- Silent failures are forbidden in financial calculations
- Every error must produce an audit trail

### 2. Fail Fast, Fail Safe
- Detect errors early in the process
- Ensure system remains in consistent state after failures
- Implement proper rollback mechanisms

### 3. Regulatory Compliance
- All errors affecting financial calculations must be reported
- Maintain error logs for minimum 7 years (insurance regulation)
- Include transaction IDs in all error messages

## Exception Hierarchy

### 1. Base Insurance Exceptions
```python
from typing import Optional, Any
from datetime import datetime
import uuid

class InsuranceException(Exception):
    """Base exception for all insurance operations"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        transaction_id: Optional[str] = None,
        context: Optional[dict[str, Any]] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.transaction_id = transaction_id or str(uuid.uuid4())
        self.context = context or {}
        self.timestamp = datetime.utcnow()
    
    def to_audit_log(self) -> dict[str, Any]:
        """Convert exception to audit log format"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": str(self),
            "transaction_id": self.transaction_id,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }
```

### 2. Domain-Specific Exceptions
```python
class PolicyException(InsuranceException):
    """Base for all policy-related errors"""
    pass

class PolicyNotFoundError(PolicyException):
    """Raised when policy lookup fails"""
    def __init__(self, policy_number: str):
        super().__init__(
            message=f"Policy not found: {policy_number}",
            error_code="POL001",
            context={"policy_number": policy_number}
        )

class PolicyValidationError(PolicyException):
    """Raised when policy data fails validation"""
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            message=f"Policy validation failed for {field}: {reason}",
            error_code="POL002",
            context={"field": field, "value": str(value), "reason": reason}
        )

class PremiumCalculationError(InsuranceException):
    """Raised when premium calculation fails"""
    def __init__(self, reason: str, factors: dict[str, Any]):
        super().__init__(
            message=f"Premium calculation failed: {reason}",
            error_code="PRM001",
            context={"calculation_factors": factors}
        )

class ClaimException(InsuranceException):
    """Base for all claim-related errors"""
    pass

class ClaimValidationError(ClaimException):
    """Raised when claim data fails validation"""
    def __init__(self, claim_number: str, validation_errors: list[str]):
        super().__init__(
            message=f"Claim validation failed: {', '.join(validation_errors)}",
            error_code="CLM001",
            context={
                "claim_number": claim_number,
                "validation_errors": validation_errors
            }
        )
```

## Error Handling Patterns

### 1. Validation Pattern
```python
from typing import TypeVar, Protocol
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: list[str]
    warnings: list[str]

class Validator(Protocol[T]):
    """Protocol for validators"""
    def validate(self, data: T) -> ValidationResult: ...

def validate_policy_data(policy_data: dict[str, Any]) -> PolicyData:
    """Validate policy data with comprehensive error collection"""
    errors: list[str] = []
    warnings: list[str] = []
    
    # Required field validation
    required_fields = ['policy_number', 'effective_date', 'premium']
    for field in required_fields:
        if field not in policy_data:
            errors.append(f"Missing required field: {field}")
    
    # Premium validation
    if 'premium' in policy_data:
        try:
            premium = Decimal(str(policy_data['premium']))
            if premium <= 0:
                errors.append("Premium must be positive")
            elif premium < Decimal('100'):
                warnings.append("Premium below minimum threshold")
        except (ValueError, InvalidOperation):
            errors.append("Invalid premium format")
    
    # Date validation
    if 'effective_date' in policy_data:
        try:
            effective_date = datetime.fromisoformat(policy_data['effective_date'])
            if effective_date < datetime.now():
                warnings.append("Effective date is in the past")
        except ValueError:
            errors.append("Invalid date format for effective_date")
    
    if errors:
        raise PolicyValidationError(
            field="multiple",
            value=policy_data,
            reason="; ".join(errors)
        )
    
    # Log warnings but proceed
    if warnings:
        logger.warning(
            "Policy validation warnings",
            extra={
                "warnings": warnings,
                "policy_number": policy_data.get('policy_number')
            }
        )
    
    return PolicyData(**policy_data)
```

### 2. Transaction Pattern
```python
from contextlib import contextmanager
from typing import Generator, Optional

class TransactionManager:
    """Manage database transactions with proper error handling"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.transaction_id: Optional[str] = None
    
    @contextmanager
    def transaction(self) -> Generator[str, None, None]:
        """Context manager for database transactions"""
        self.transaction_id = str(uuid.uuid4())
        
        try:
            self.db.begin()
            logger.info(f"Transaction started: {self.transaction_id}")
            yield self.transaction_id
            self.db.commit()
            logger.info(f"Transaction committed: {self.transaction_id}")
            
        except InsuranceException as e:
            # Add transaction context to insurance exceptions
            e.transaction_id = self.transaction_id
            self.db.rollback()
            logger.error(
                f"Transaction rolled back: {self.transaction_id}",
                extra=e.to_audit_log()
            )
            raise
            
        except Exception as e:
            # Wrap unexpected exceptions
            self.db.rollback()
            logger.error(
                f"Unexpected error in transaction: {self.transaction_id}",
                exc_info=True
            )
            raise InsuranceException(
                message=f"Transaction failed: {str(e)}",
                error_code="TRX001",
                transaction_id=self.transaction_id,
                context={"original_error": str(e)}
            ) from e
```

### 3. Retry Pattern
```python
import asyncio
from typing import TypeVar, Callable, Awaitable
from functools import wraps

T = TypeVar('T')

class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    retry_on: tuple[type[Exception], ...] = (ConnectionError, TimeoutError)

def with_retry(config: RetryConfig = RetryConfig()):
    """Decorator for retrying operations with exponential backoff"""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                    
                except config.retry_on as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"Max retries exceeded for {func.__name__}",
                            extra={
                                "attempts": config.max_attempts,
                                "final_error": str(e)
                            }
                        )
                        raise
                    
                    delay = min(
                        config.initial_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    logger.warning(
                        f"Retrying {func.__name__} after {delay}s",
                        extra={
                            "attempt": attempt + 1,
                            "max_attempts": config.max_attempts,
                            "error": str(e)
                        }
                    )
                    
                    await asyncio.sleep(delay)
            
            # Should never reach here
            raise last_exception  # type: ignore
        
        return wrapper
    return decorator

# Usage example
@with_retry(RetryConfig(retry_on=(RatingEngineError,)))
async def get_insurance_rate(policy_data: PolicyData) -> Decimal:
    """Get rate from external rating engine with retry"""
    response = await rating_engine.calculate_rate(policy_data)
    return Decimal(response.rate)
```

## Error Propagation Strategies

### 1. Layered Error Handling
```python
# Repository Layer
class PolicyRepository:
    async def find_by_number(self, policy_number: str) -> Policy:
        try:
            result = await self.db.query(
                "SELECT * FROM policies WHERE policy_number = ?",
                policy_number
            )
            if not result:
                raise PolicyNotFoundError(policy_number)
            return Policy.from_db_row(result)
            
        except DatabaseError as e:
            logger.error(f"Database error finding policy: {policy_number}", exc_info=True)
            raise InsuranceException(
                message="Failed to retrieve policy",
                error_code="DB001",
                context={"policy_number": policy_number, "db_error": str(e)}
            ) from e

# Service Layer
class PolicyService:
    def __init__(self, repo: PolicyRepository):
        self.repo = repo
    
    async def get_policy_details(self, policy_number: str) -> PolicyDetails:
        try:
            policy = await self.repo.find_by_number(policy_number)
            
            # Business logic validation
            if policy.status == PolicyStatus.CANCELLED:
                raise PolicyException(
                    message="Cannot retrieve details for cancelled policy",
                    error_code="POL003",
                    context={"policy_number": policy_number, "status": policy.status}
                )
            
            return self._build_policy_details(policy)
            
        except PolicyNotFoundError:
            # Let specific errors propagate
            raise
            
        except InsuranceException as e:
            # Add service context to existing exceptions
            e.context["service"] = "PolicyService.get_policy_details"
            raise

# API Layer
@app.route("/api/policies/<policy_number>")
async def get_policy(policy_number: str):
    try:
        details = await policy_service.get_policy_details(policy_number)
        return jsonify(details.to_dict()), 200
        
    except PolicyNotFoundError as e:
        return jsonify({
            "error": "Policy not found",
            "error_code": e.error_code,
            "transaction_id": e.transaction_id
        }), 404
        
    except PolicyException as e:
        return jsonify({
            "error": str(e),
            "error_code": e.error_code,
            "transaction_id": e.transaction_id
        }), 400
        
    except InsuranceException as e:
        # Log full context for internal errors
        logger.error("Internal error", extra=e.to_audit_log())
        return jsonify({
            "error": "Internal server error",
            "error_code": "INT001",
            "transaction_id": e.transaction_id
        }), 500
```

### 2. Circuit Breaker Pattern
```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: timedelta = timedelta(seconds=60),
        expected_exception: type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise InsuranceException(
                    message="Circuit breaker is open",
                    error_code="CB001",
                    context={
                        "service": func.__name__,
                        "failures": self.failure_count,
                        "last_failure": self.last_failure_time.isoformat()
                        if self.last_failure_time else None
                    }
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise InsuranceException(
                message=f"Service call failed: {func.__name__}",
                error_code="CB002",
                context={
                    "service": func.__name__,
                    "state": self.state.value,
                    "error": str(e)
                }
            ) from e
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time is not None and
            datetime.utcnow() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
```

## Logging and Monitoring

### 1. Structured Logging
```python
import structlog
from typing import Any

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class ErrorLogger:
    """Centralized error logging with context"""
    
    @staticmethod
    def log_validation_error(
        error: ValidationError,
        context: dict[str, Any]
    ) -> None:
        """Log validation errors with full context"""
        logger.error(
            "validation_failed",
            error_type=error.__class__.__name__,
            error_message=str(error),
            validation_context=context,
            stack_info=True
        )
    
    @staticmethod
    def log_calculation_error(
        error: CalculationError,
        inputs: dict[str, Any],
        transaction_id: str
    ) -> None:
        """Log calculation errors for audit trail"""
        logger.error(
            "calculation_failed",
            error_type=error.__class__.__name__,
            error_message=str(error),
            calculation_inputs=inputs,
            transaction_id=transaction_id,
            stack_info=True,
            # Include for compliance
            timestamp=datetime.utcnow().isoformat(),
            system_state="CALCULATION_ERROR"
        )
```

### 2. Error Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
error_counter = Counter(
    'insurance_errors_total',
    'Total number of errors',
    ['error_type', 'error_code', 'service']
)

error_response_time = Histogram(
    'insurance_error_handling_duration_seconds',
    'Time spent handling errors',
    ['error_type']
)

circuit_breaker_state = Gauge(
    'insurance_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['service']
)

def track_error(error: InsuranceException, service: str) -> None:
    """Track error metrics"""
    error_counter.labels(
        error_type=error.__class__.__name__,
        error_code=error.error_code,
        service=service
    ).inc()
```

## Recovery Strategies

### 1. Compensation Pattern
```python
class CompensationAction(Protocol):
    """Protocol for compensation actions"""
    async def execute(self) -> None: ...
    async def compensate(self) -> None: ...

class PolicyCreationSaga:
    """Saga pattern for complex policy creation"""
    
    def __init__(self):
        self.completed_actions: list[CompensationAction] = []
    
    async def execute(self, policy_data: PolicyData) -> Policy:
        """Execute policy creation with compensation on failure"""
        try:
            # Step 1: Create policy record
            create_policy = CreatePolicyAction(policy_data)
            await create_policy.execute()
            self.completed_actions.append(create_policy)
            
            # Step 2: Calculate premium
            calc_premium = CalculatePremiumAction(policy_data)
            await calc_premium.execute()
            self.completed_actions.append(calc_premium)
            
            # Step 3: Create billing record
            create_billing = CreateBillingAction(policy_data)
            await create_billing.execute()
            self.completed_actions.append(create_billing)
            
            # Step 4: Send confirmation
            send_confirm = SendConfirmationAction(policy_data)
            await send_confirm.execute()
            self.completed_actions.append(send_confirm)
            
            return Policy(policy_data)
            
        except Exception as e:
            # Compensate in reverse order
            logger.error(f"Policy creation failed, compensating...", exc_info=True)
            
            for action in reversed(self.completed_actions):
                try:
                    await action.compensate()
                except Exception as comp_error:
                    logger.error(
                        f"Compensation failed for {action.__class__.__name__}",
                        exc_info=True
                    )
            
            raise PolicyCreationError(
                message="Policy creation failed and was rolled back",
                error_code="POL004",
                context={
                    "original_error": str(e),
                    "compensated_actions": len(self.completed_actions)
                }
            ) from e
```

### 2. Graceful Degradation
```python
class RatingService:
    """Rating service with fallback strategies"""
    
    def __init__(
        self,
        primary_engine: RatingEngine,
        fallback_engine: RatingEngine,
        cache: RatingCache
    ):
        self.primary = primary_engine
        self.fallback = fallback_engine
        self.cache = cache
        self.circuit_breaker = CircuitBreaker()
    
    async def get_rate(self, policy_data: PolicyData) -> RateResult:
        """Get rate with multiple fallback strategies"""
        
        # Try primary rating engine
        try:
            return await self.circuit_breaker.call(
                self.primary.calculate_rate,
                policy_data
            )
        except InsuranceException:
            logger.warning("Primary rating engine failed, trying fallback")
        
        # Try fallback rating engine
        try:
            result = await self.fallback.calculate_rate(policy_data)
            logger.warning("Using fallback rating engine")
            return result
        except Exception:
            logger.warning("Fallback rating engine failed, checking cache")
        
        # Try cache for similar policies
        try:
            cached_rate = await self.cache.get_similar_rate(policy_data)
            if cached_rate:
                logger.warning("Using cached rate for similar policy")
                return RateResult(
                    rate=cached_rate,
                    source="CACHE",
                    confidence=0.8
                )
        except Exception:
            logger.error("Cache lookup failed")
        
        # Last resort: return default rate with low confidence
        logger.error("All rating methods failed, using default rate")
        return RateResult(
            rate=self._get_default_rate(policy_data),
            source="DEFAULT",
            confidence=0.5
        )
```

## Testing Error Scenarios

### 1. Error Injection
```python
import pytest
from unittest.mock import Mock, patch

class ErrorInjector:
    """Inject errors for testing error handling"""
    
    def __init__(self):
        self.error_sequence: list[Exception] = []
        self.call_count = 0
    
    def add_error(self, error: Exception) -> None:
        """Add error to injection sequence"""
        self.error_sequence.append(error)
    
    def maybe_raise(self) -> None:
        """Raise error if configured"""
        if self.call_count < len(self.error_sequence):
            error = self.error_sequence[self.call_count]
            self.call_count += 1
            raise error
        self.call_count += 1

@pytest.fixture
def error_injector():
    return ErrorInjector()

async def test_premium_calculation_with_errors(error_injector):
    """Test premium calculation error handling"""
    
    # Inject database error
    error_injector.add_error(DatabaseError("Connection lost"))
    
    service = PremiumService()
    with patch.object(service.db, 'query', side_effect=error_injector.maybe_raise):
        with pytest.raises(InsuranceException) as exc_info:
            await service.calculate_premium(PolicyData())
        
        assert exc_info.value.error_code == "DB001"
        assert "Connection lost" in exc_info.value.context["db_error"]
```

### 2. Chaos Engineering
```python
import random

class ChaosMonkey:
    """Introduce controlled chaos for testing resilience"""
    
    def __init__(self, failure_rate: float = 0.1):
        self.failure_rate = failure_rate
        self.enabled = False
    
    def maybe_fail(self, operation: str) -> None:
        """Randomly fail operations when enabled"""
        if self.enabled and random.random() < self.failure_rate:
            error_type = random.choice([
                DatabaseError("Chaos: Database unavailable"),
                TimeoutError("Chaos: Operation timeout"),
                ConnectionError("Chaos: Network failure")
            ])
            logger.warning(f"Chaos monkey triggered: {operation}")
            raise error_type
    
    @contextmanager
    def unleash(self):
        """Context manager to enable chaos"""
        self.enabled = True
        try:
            yield
        finally:
            self.enabled = False

# Usage in testing
async def test_system_resilience():
    chaos = ChaosMonkey(failure_rate=0.3)
    
    with chaos.unleash():
        # Run normal operations with random failures
        results = []
        for i in range(100):
            try:
                chaos.maybe_fail("policy_creation")
                result = await create_policy(test_policy_data())
                results.append(("success", result))
            except Exception as e:
                results.append(("failure", str(e)))
        
        # Assert system handled failures gracefully
        success_rate = len([r for r in results if r[0] == "success"]) / 100
        assert success_rate > 0.5  # At least 50% success despite 30% chaos
```