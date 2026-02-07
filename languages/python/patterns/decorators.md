---
name: Decorators
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# Python Decorators for Insurance Systems

## Overview

Decorators provide a clean way to modify or enhance functions and methods without changing their source code. In insurance systems, decorators are particularly useful for cross-cutting concerns like validation, caching, logging, and transaction management.

## Performance Decorators

### Cache Decorator
```python
from functools import lru_cache, wraps
from typing import Callable, Any, Optional
import time
import redis
import json
import hashlib

class PolicyCache:
    """Advanced caching decorator for policy calculations"""
    
    def __init__(self, ttl: int = 3600, redis_client: Optional[redis.Redis] = None):
        self.ttl = ttl
        self.redis_client = redis_client
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = self._create_cache_key(func.__name__, args, kwargs)
            
            # Try Redis first if available
            if self.redis_client:
                cached = self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            
            # Calculate result
            result = func(*args, **kwargs)
            
            # Store in Redis if available
            if self.redis_client:
                self.redis_client.setex(
                    cache_key, 
                    self.ttl, 
                    json.dumps(result)
                )
            
            return result
        
        return wrapper
    
    def _create_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Create a unique cache key based on function and arguments"""
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

# Usage example
@PolicyCache(ttl=1800)
def calculate_premium(
    age: int, 
    coverage_amount: float, 
    risk_factors: list
) -> float:
    """Calculate insurance premium based on risk factors"""
    base_premium = coverage_amount * 0.001
    age_factor = 1 + (age - 30) * 0.02
    risk_multiplier = 1 + len(risk_factors) * 0.1
    
    return base_premium * age_factor * risk_multiplier
```

### Retry Decorator
```python
import time
from functools import wraps
from typing import Callable, Type, Tuple, Union
import logging

logger = logging.getLogger(__name__)

def retry(
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    max_delay: float = 60.0
) -> Callable:
    """
    Retry decorator with exponential backoff
    
    Args:
        exceptions: Exception types to catch
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries
        backoff: Multiplier for delay after each retry
        max_delay: Maximum delay between retries
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay:.2f} seconds..."
                        )
                        time.sleep(current_delay)
                        current_delay = min(current_delay * backoff, max_delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator

# Usage example
@retry(exceptions=(ConnectionError, TimeoutError), max_attempts=5, delay=2.0)
def fetch_credit_score(ssn: str) -> int:
    """Fetch credit score from external service"""
    # Simulated external API call
    response = external_credit_api.get_score(ssn)
    return response.score
```

### Timeout Decorator
```python
import signal
import functools
from typing import Callable, Any

class TimeoutError(Exception):
    pass

def timeout(seconds: int) -> Callable:
    """Decorator to limit function execution time"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            def timeout_handler(signum, frame):
                raise TimeoutError(f"{func.__name__} timed out after {seconds} seconds")
            
            # Set up the signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                # Restore the old handler and cancel the alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
        
        return wrapper
    return decorator

# Usage example
@timeout(30)
def complex_risk_analysis(policy_data: dict) -> dict:
    """Perform complex risk analysis with timeout protection"""
    # Time-intensive risk calculations
    return analyze_risk_factors(policy_data)
```

## Validation Decorators

### Insurance Rule Validator
```python
from functools import wraps
from typing import Callable, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, date

@dataclass
class ValidationRule:
    field: str
    condition: Callable
    error_message: str

class PolicyValidator:
    """Decorator for validating insurance policy data"""
    
    def __init__(self, rules: List[ValidationRule]):
        self.rules = rules
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract policy data from arguments
            policy_data = self._extract_policy_data(args, kwargs)
            
            # Validate against all rules
            errors = []
            for rule in self.rules:
                if rule.field in policy_data:
                    if not rule.condition(policy_data[rule.field]):
                        errors.append(f"{rule.field}: {rule.error_message}")
            
            if errors:
                raise ValueError(f"Policy validation failed: {'; '.join(errors)}")
            
            return func(*args, **kwargs)
        
        return wrapper
    
    def _extract_policy_data(self, args: tuple, kwargs: dict) -> dict:
        """Extract policy data from function arguments"""
        # Assume first argument is policy data dict
        if args and isinstance(args[0], dict):
            return args[0]
        return kwargs.get('policy_data', {})

# Define common insurance validation rules
POLICY_RULES = [
    ValidationRule(
        field='age',
        condition=lambda x: 18 <= x <= 100,
        error_message='Applicant must be between 18 and 100 years old'
    ),
    ValidationRule(
        field='coverage_amount',
        condition=lambda x: 10000 <= x <= 10000000,
        error_message='Coverage must be between $10,000 and $10,000,000'
    ),
    ValidationRule(
        field='effective_date',
        condition=lambda x: datetime.strptime(x, '%Y-%m-%d').date() >= date.today(),
        error_message='Effective date must be today or in the future'
    ),
    ValidationRule(
        field='smoker',
        condition=lambda x: isinstance(x, bool),
        error_message='Smoker status must be true or false'
    )
]

# Usage example
@PolicyValidator(POLICY_RULES)
def create_life_insurance_policy(policy_data: dict) -> dict:
    """Create a new life insurance policy after validation"""
    return {
        'policy_id': generate_policy_id(),
        'status': 'active',
        **policy_data
    }
```

### Underwriting Validator
```python
from enum import Enum
from typing import List, Optional

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DECLINED = "declined"

def validate_underwriting_limits(
    max_coverage_by_risk: Dict[RiskLevel, float],
    min_age: int = 18,
    max_age: int = 85
) -> Callable:
    """Decorator to validate underwriting limits based on risk assessment"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            applicant_data: dict,
            requested_coverage: float,
            *args, 
            **kwargs
        ):
            # Age validation
            age = applicant_data.get('age', 0)
            if not min_age <= age <= max_age:
                raise ValueError(
                    f"Applicant age {age} outside acceptable range "
                    f"({min_age}-{max_age})"
                )
            
            # Risk-based coverage validation
            risk_level = assess_risk_level(applicant_data)
            max_allowed = max_coverage_by_risk.get(risk_level, 0)
            
            if risk_level == RiskLevel.DECLINED:
                raise ValueError("Application declined based on risk assessment")
            
            if requested_coverage > max_allowed:
                raise ValueError(
                    f"Requested coverage ${requested_coverage:,.2f} exceeds "
                    f"maximum allowed ${max_allowed:,.2f} for {risk_level.value} risk"
                )
            
            return func(applicant_data, requested_coverage, *args, **kwargs)
        
        return wrapper
    return decorator

# Usage example
@validate_underwriting_limits(
    max_coverage_by_risk={
        RiskLevel.LOW: 5000000,
        RiskLevel.MEDIUM: 2000000,
        RiskLevel.HIGH: 500000
    }
)
def underwrite_policy(
    applicant_data: dict, 
    requested_coverage: float
) -> dict:
    """Underwrite an insurance policy after validation"""
    premium = calculate_premium(applicant_data, requested_coverage)
    return {
        'approved': True,
        'coverage': requested_coverage,
        'annual_premium': premium,
        'risk_level': assess_risk_level(applicant_data).value
    }
```

## Async Decorators

### Async Rate Limiter
```python
import asyncio
from functools import wraps
from typing import Callable, Awaitable
from collections import defaultdict
from datetime import datetime, timedelta

class AsyncRateLimiter:
    """Rate limiter for async functions"""
    
    def __init__(self, calls: int, period: timedelta):
        self.calls = calls
        self.period = period
        self.calls_made = defaultdict(list)
        self.lock = asyncio.Lock()
    
    def __call__(self, func: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Use first argument as key (e.g., customer_id)
            key = args[0] if args else 'global'
            
            async with self.lock:
                now = datetime.now()
                
                # Clean old calls
                self.calls_made[key] = [
                    call_time for call_time in self.calls_made[key]
                    if now - call_time < self.period
                ]
                
                # Check rate limit
                if len(self.calls_made[key]) >= self.calls:
                    wait_time = (
                        self.calls_made[key][0] + self.period - now
                    ).total_seconds()
                    raise Exception(
                        f"Rate limit exceeded. Try again in {wait_time:.1f} seconds"
                    )
                
                # Record call
                self.calls_made[key].append(now)
            
            return await func(*args, **kwargs)
        
        return wrapper

# Usage example
@AsyncRateLimiter(calls=10, period=timedelta(minutes=1))
async def check_claim_eligibility(
    claim_id: str, 
    policy_id: str
) -> dict:
    """Check claim eligibility with rate limiting"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"/api/claims/{claim_id}") as response:
            return await response.json()
```

### Async Batch Processor
```python
import asyncio
from typing import List, Any, Callable, Awaitable
from collections import defaultdict

class AsyncBatchProcessor:
    """Decorator to batch async operations for efficiency"""
    
    def __init__(self, batch_size: int = 10, delay: float = 0.1):
        self.batch_size = batch_size
        self.delay = delay
        self.pending = defaultdict(list)
        self.results = {}
        self.lock = asyncio.Lock()
    
    def __call__(self, func: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
        @wraps(func)
        async def wrapper(item_id: str, *args, **kwargs):
            # Create a future for this request
            future = asyncio.Future()
            
            async with self.lock:
                batch_key = f"{func.__name__}:{args}:{kwargs}"
                self.pending[batch_key].append((item_id, future))
                
                # Process batch if size reached
                if len(self.pending[batch_key]) >= self.batch_size:
                    await self._process_batch(func, batch_key, args, kwargs)
                else:
                    # Schedule batch processing after delay
                    asyncio.create_task(
                        self._delayed_batch_process(func, batch_key, args, kwargs)
                    )
            
            return await future
        
        return wrapper
    
    async def _process_batch(
        self, 
        func: Callable, 
        batch_key: str, 
        args: tuple, 
        kwargs: dict
    ):
        """Process a batch of requests"""
        items = self.pending.pop(batch_key, [])
        if not items:
            return
        
        item_ids = [item[0] for item in items]
        futures = [item[1] for item in items]
        
        try:
            # Call the original function with batched IDs
            results = await func(item_ids, *args, **kwargs)
            
            # Distribute results to futures
            for future, result in zip(futures, results):
                future.set_result(result)
        except Exception as e:
            for future in futures:
                future.set_exception(e)
    
    async def _delayed_batch_process(
        self, 
        func: Callable, 
        batch_key: str, 
        args: tuple, 
        kwargs: dict
    ):
        """Process batch after delay"""
        await asyncio.sleep(self.delay)
        async with self.lock:
            await self._process_batch(func, batch_key, args, kwargs)

# Usage example
@AsyncBatchProcessor(batch_size=20, delay=0.5)
async def fetch_policy_details(policy_ids: List[str]) -> List[dict]:
    """Fetch multiple policy details in a single batch request"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "/api/policies/batch",
            json={"policy_ids": policy_ids}
        ) as response:
            return await response.json()
```

## Logging and Monitoring Decorators

### Comprehensive Logger
```python
import logging
import time
import json
from functools import wraps
from typing import Callable, Any, Optional
import traceback
from datetime import datetime

class PolicyOperationLogger:
    """Advanced logging decorator for policy operations"""
    
    def __init__(
        self, 
        logger: Optional[logging.Logger] = None,
        log_args: bool = True,
        log_result: bool = True,
        log_execution_time: bool = True,
        sensitive_fields: List[str] = None
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.log_args = log_args
        self.log_result = log_result
        self.log_execution_time = log_execution_time
        self.sensitive_fields = sensitive_fields or ['ssn', 'password', 'credit_card']
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation_id = f"{func.__name__}_{int(start_time * 1000)}"
            
            # Log operation start
            log_data = {
                'operation_id': operation_id,
                'function': func.__name__,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'started'
            }
            
            if self.log_args:
                log_data['args'] = self._sanitize_data(args)
                log_data['kwargs'] = self._sanitize_data(kwargs)
            
            self.logger.info(f"Operation started: {json.dumps(log_data)}")
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful completion
                end_time = time.time()
                log_data.update({
                    'status': 'completed',
                    'execution_time': round(end_time - start_time, 3)
                })
                
                if self.log_result:
                    log_data['result'] = self._sanitize_data(result)
                
                self.logger.info(f"Operation completed: {json.dumps(log_data)}")
                
                return result
                
            except Exception as e:
                # Log failure
                end_time = time.time()
                log_data.update({
                    'status': 'failed',
                    'execution_time': round(end_time - start_time, 3),
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                })
                
                self.logger.error(f"Operation failed: {json.dumps(log_data)}")
                raise
        
        return wrapper
    
    def _sanitize_data(self, data: Any) -> Any:
        """Remove sensitive information from logged data"""
        if isinstance(data, dict):
            return {
                k: '***REDACTED***' if k in self.sensitive_fields else self._sanitize_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, (list, tuple)):
            return [self._sanitize_data(item) for item in data]
        else:
            return data

# Usage example
@PolicyOperationLogger(
    log_args=True,
    log_result=True,
    sensitive_fields=['ssn', 'date_of_birth', 'medical_history']
)
def process_insurance_application(application_data: dict) -> dict:
    """Process a new insurance application"""
    # Application processing logic
    return {
        'application_id': generate_application_id(),
        'status': 'under_review',
        'estimated_premium': calculate_initial_premium(application_data)
    }
```

### Performance Monitor
```python
import time
from functools import wraps
from typing import Callable, Dict, Any
import psutil
import threading
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PerformanceMetrics:
    function_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    cpu_percent: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    exception: Optional[str] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

class PerformanceMonitor:
    """Monitor function performance and resource usage"""
    
    def __init__(self, track_resources: bool = True):
        self.track_resources = track_resources
        self.metrics_store = []
        self.lock = threading.Lock()
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics = PerformanceMetrics(
                function_name=func.__name__,
                start_time=datetime.utcnow()
            )
            
            # Get initial resource usage
            if self.track_resources:
                process = psutil.Process()
                initial_memory = process.memory_info().rss / 1024 / 1024
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate metrics
                metrics.end_time = datetime.utcnow()
                metrics.execution_time = (
                    metrics.end_time - metrics.start_time
                ).total_seconds()
                
                if self.track_resources:
                    metrics.cpu_percent = process.cpu_percent()
                    metrics.memory_usage_mb = (
                        process.memory_info().rss / 1024 / 1024 - initial_memory
                    )
                
                # Store metrics
                with self.lock:
                    self.metrics_store.append(metrics)
                
                # Alert if performance threshold exceeded
                if metrics.execution_time > 5.0:  # 5 second threshold
                    logger.warning(
                        f"{func.__name__} took {metrics.execution_time:.2f}s to execute"
                    )
                
                return result
                
            except Exception as e:
                metrics.exception = str(e)
                metrics.end_time = datetime.utcnow()
                metrics.execution_time = (
                    metrics.end_time - metrics.start_time
                ).total_seconds()
                
                with self.lock:
                    self.metrics_store.append(metrics)
                raise
        
        return wrapper
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        with self.lock:
            if not self.metrics_store:
                return {}
            
            return {
                'total_calls': len(self.metrics_store),
                'avg_execution_time': sum(
                    m.execution_time for m in self.metrics_store 
                    if m.execution_time
                ) / len(self.metrics_store),
                'max_execution_time': max(
                    m.execution_time for m in self.metrics_store 
                    if m.execution_time
                ),
                'total_errors': sum(
                    1 for m in self.metrics_store if m.exception
                ),
                'avg_memory_usage_mb': sum(
                    m.memory_usage_mb for m in self.metrics_store 
                    if m.memory_usage_mb
                ) / len([m for m in self.metrics_store if m.memory_usage_mb])
            }

# Global monitor instance
perf_monitor = PerformanceMonitor()

# Usage example
@perf_monitor
def calculate_actuarial_reserves(
    policies: List[dict], 
    mortality_table: dict
) -> float:
    """Calculate actuarial reserves for a portfolio"""
    total_reserves = 0.0
    
    for policy in policies:
        age = policy['current_age']
        sum_assured = policy['sum_assured']
        remaining_term = policy['remaining_term']
        
        # Complex actuarial calculations
        mortality_rate = mortality_table.get(age, 0.001)
        present_value = sum_assured * (1 - mortality_rate) ** remaining_term
        total_reserves += present_value * 0.9  # Reserve factor
    
    return total_reserves
```

## Transaction Decorators

### Database Transaction
```python
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Optional
import logging
from sqlalchemy.orm import Session

class TransactionManager:
    """Decorator for managing database transactions"""
    
    def __init__(
        self, 
        db_session: Session,
        isolation_level: Optional[str] = None,
        readonly: bool = False,
        retry_on_deadlock: bool = True
    ):
        self.db_session = db_session
        self.isolation_level = isolation_level
        self.readonly = readonly
        self.retry_on_deadlock = retry_on_deadlock
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            max_retries = 3 if self.retry_on_deadlock else 1
            
            for attempt in range(max_retries):
                try:
                    with self._transaction_scope():
                        return func(*args, **kwargs)
                except DeadlockError as e:
                    if attempt < max_retries - 1:
                        logging.warning(
                            f"Deadlock detected in {func.__name__}, "
                            f"retrying (attempt {attempt + 2}/{max_retries})"
                        )
                        time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    else:
                        raise
        
        return wrapper
    
    @contextmanager
    def _transaction_scope(self):
        """Provide a transactional scope around operations"""
        if self.isolation_level:
            self.db_session.connection().execution_options(
                isolation_level=self.isolation_level
            )
        
        try:
            yield self.db_session
            if not self.readonly:
                self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            raise
        finally:
            self.db_session.close()

# Usage example
@TransactionManager(
    db_session=get_db_session(),
    isolation_level="REPEATABLE READ",
    retry_on_deadlock=True
)
def transfer_policy_ownership(
    policy_id: str, 
    new_owner_id: str, 
    effective_date: date
) -> dict:
    """Transfer policy ownership within a transaction"""
    # Get current policy
    policy = db_session.query(Policy).filter_by(id=policy_id).first()
    if not policy:
        raise ValueError(f"Policy {policy_id} not found")
    
    # Record ownership history
    history = OwnershipHistory(
        policy_id=policy_id,
        previous_owner_id=policy.owner_id,
        new_owner_id=new_owner_id,
        transfer_date=effective_date,
        created_at=datetime.utcnow()
    )
    db_session.add(history)
    
    # Update policy owner
    policy.owner_id = new_owner_id
    policy.last_modified = datetime.utcnow()
    
    # Update beneficiaries if needed
    if policy.beneficiary_id == policy.owner_id:
        policy.beneficiary_id = new_owner_id
    
    return {
        'policy_id': policy_id,
        'new_owner_id': new_owner_id,
        'transfer_id': history.id,
        'status': 'completed'
    }
```

### Saga Pattern Decorator
```python
from typing import List, Callable, Any, Dict
from dataclasses import dataclass
import uuid

@dataclass
class SagaStep:
    name: str
    action: Callable
    compensate: Callable
    args: tuple = ()
    kwargs: dict = None

class SagaOrchestrator:
    """Implement saga pattern for distributed transactions"""
    
    def __init__(self, steps: List[SagaStep]):
        self.steps = steps
        self.completed_steps = []
        self.saga_id = str(uuid.uuid4())
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Execute all saga steps
                results = {}
                for step in self.steps:
                    logging.info(
                        f"Saga {self.saga_id}: Executing step {step.name}"
                    )
                    
                    step_args = step.args or ()
                    step_kwargs = step.kwargs or {}
                    
                    result = step.action(*step_args, **step_kwargs)
                    results[step.name] = result
                    self.completed_steps.append(step)
                
                # Execute the main function
                main_result = func(*args, **kwargs)
                
                logging.info(f"Saga {self.saga_id}: Completed successfully")
                return main_result
                
            except Exception as e:
                logging.error(
                    f"Saga {self.saga_id}: Failed at step {step.name}. "
                    f"Starting compensation..."
                )
                
                # Compensate in reverse order
                for step in reversed(self.completed_steps):
                    try:
                        logging.info(
                            f"Saga {self.saga_id}: Compensating step {step.name}"
                        )
                        step.compensate()
                    except Exception as comp_error:
                        logging.error(
                            f"Saga {self.saga_id}: Compensation failed for "
                            f"{step.name}: {comp_error}"
                        )
                
                raise
        
        return wrapper

# Usage example
def create_policy_saga(customer_data: dict, policy_data: dict) -> dict:
    """Create a new policy using saga pattern"""
    
    # Define saga steps
    customer_id = None
    payment_id = None
    policy_id = None
    
    def create_customer():
        nonlocal customer_id
        customer_id = customer_service.create(customer_data)
        return customer_id
    
    def delete_customer():
        if customer_id:
            customer_service.delete(customer_id)
    
    def process_payment():
        nonlocal payment_id
        payment_id = payment_service.charge(
            customer_id, 
            policy_data['initial_premium']
        )
        return payment_id
    
    def refund_payment():
        if payment_id:
            payment_service.refund(payment_id)
    
    def create_policy():
        nonlocal policy_id
        policy_id = policy_service.create({
            **policy_data,
            'customer_id': customer_id,
            'payment_id': payment_id
        })
        return policy_id
    
    def cancel_policy():
        if policy_id:
            policy_service.cancel(policy_id)
    
    # Create saga
    saga = SagaOrchestrator([
        SagaStep('create_customer', create_customer, delete_customer),
        SagaStep('process_payment', process_payment, refund_payment),
        SagaStep('create_policy', create_policy, cancel_policy)
    ])
    
    @saga
    def execute_policy_creation():
        return {
            'customer_id': customer_id,
            'policy_id': policy_id,
            'payment_id': payment_id,
            'status': 'active'
        }
    
    return execute_policy_creation()
```

## Rate Limiting Decorators

### Token Bucket Rate Limiter
```python
import time
from threading import Lock
from functools import wraps
from typing import Callable, Dict

class TokenBucket:
    """Token bucket implementation for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

class RateLimiter:
    """Rate limiting decorator using token bucket algorithm"""
    
    def __init__(
        self, 
        requests_per_second: float,
        burst_size: int = None,
        key_func: Callable = None
    ):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size or int(requests_per_second * 2)
        self.key_func = key_func or (lambda *args, **kwargs: 'global')
        self.buckets: Dict[str, TokenBucket] = {}
        self.lock = Lock()
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get rate limit key
            key = self.key_func(*args, **kwargs)
            
            # Get or create bucket for this key
            with self.lock:
                if key not in self.buckets:
                    self.buckets[key] = TokenBucket(
                        self.burst_size, 
                        self.requests_per_second
                    )
                bucket = self.buckets[key]
            
            # Try to consume token
            if not bucket.consume():
                raise Exception(
                    f"Rate limit exceeded for {key}. "
                    f"Maximum {self.requests_per_second} requests per second."
                )
            
            return func(*args, **kwargs)
        
        return wrapper

# Usage example
@RateLimiter(
    requests_per_second=10,
    burst_size=20,
    key_func=lambda agent_id, *args, **kwargs: f"agent:{agent_id}"
)
def submit_quote(agent_id: str, quote_data: dict) -> dict:
    """Submit insurance quote with per-agent rate limiting"""
    return quote_service.create_quote(agent_id, quote_data)
```

## Authentication/Authorization Decorators

### Role-Based Access Control
```python
from functools import wraps
from typing import Callable, List, Optional, Union
from enum import Enum

class Role(Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    UNDERWRITER = "underwriter"
    MANAGER = "manager"
    ADMIN = "admin"

class PermissionDeniedError(Exception):
    pass

def require_roles(
    allowed_roles: Union[Role, List[Role]],
    check_ownership: bool = False,
    owner_param: str = 'user_id'
) -> Callable:
    """Decorator for role-based access control"""
    
    if isinstance(allowed_roles, Role):
        allowed_roles = [allowed_roles]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get current user from context
            current_user = get_current_user()
            
            if not current_user:
                raise PermissionDeniedError("Authentication required")
            
            # Check role
            if current_user.role not in allowed_roles:
                raise PermissionDeniedError(
                    f"Role {current_user.role.value} not authorized. "
                    f"Required roles: {[r.value for r in allowed_roles]}"
                )
            
            # Check ownership if required
            if check_ownership and current_user.role != Role.ADMIN:
                owner_id = kwargs.get(owner_param) or (
                    args[0] if args else None
                )
                
                if owner_id != current_user.id:
                    raise PermissionDeniedError(
                        "You can only access your own resources"
                    )
            
            # Add user context to function
            kwargs['current_user'] = current_user
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Usage examples
@require_roles([Role.UNDERWRITER, Role.MANAGER, Role.ADMIN])
def approve_high_value_policy(
    policy_id: str, 
    approval_notes: str,
    current_user: Optional[User] = None
) -> dict:
    """Approve high-value policies (underwriter+ only)"""
    policy = get_policy(policy_id)
    
    if policy.coverage_amount > 1000000 and current_user.role == Role.UNDERWRITER:
        raise PermissionDeniedError(
            "Policies over $1M require manager approval"
        )
    
    return approve_policy(policy_id, approval_notes, current_user.id)

@require_roles(Role.CUSTOMER, check_ownership=True, owner_param='customer_id')
def view_policy_details(
    customer_id: str, 
    policy_id: str,
    current_user: Optional[User] = None
) -> dict:
    """View policy details (customers can only view their own)"""
    return get_customer_policy(customer_id, policy_id)
```

### API Key Authentication
```python
import hashlib
import hmac
from functools import wraps
from typing import Callable, Optional

class APIKeyAuth:
    """Decorator for API key authentication with rate limiting"""
    
    def __init__(
        self, 
        header_name: str = 'X-API-Key',
        include_signature: bool = True
    ):
        self.header_name = header_name
        self.include_signature = include_signature
        self.api_keys = {}  # In production, use database
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Extract API key
            api_key = request.headers.get(self.header_name)
            
            if not api_key:
                raise AuthenticationError(
                    f"Missing {self.header_name} header"
                )
            
            # Validate API key
            key_data = self.validate_api_key(api_key)
            if not key_data:
                raise AuthenticationError("Invalid API key")
            
            # Check signature if required
            if self.include_signature:
                signature = request.headers.get('X-Signature')
                if not self.verify_signature(
                    request.body, 
                    signature, 
                    key_data['secret']
                ):
                    raise AuthenticationError("Invalid request signature")
            
            # Add API key context
            request.api_key_data = key_data
            
            return func(request, *args, **kwargs)
        
        return wrapper
    
    def validate_api_key(self, api_key: str) -> Optional[dict]:
        """Validate API key and return associated data"""
        # In production, query from database
        return self.api_keys.get(api_key)
    
    def verify_signature(
        self, 
        payload: bytes, 
        signature: str, 
        secret: str
    ) -> bool:
        """Verify HMAC signature"""
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)

# Usage example
@APIKeyAuth(include_signature=True)
@RateLimiter(
    requests_per_second=100,
    key_func=lambda request, *args, **kwargs: request.api_key_data['client_id']
)
def create_insurance_quote_api(request) -> dict:
    """API endpoint for creating insurance quotes"""
    quote_data = json.loads(request.body)
    
    # Validate against client's allowed products
    allowed_products = request.api_key_data.get('allowed_products', [])
    if quote_data['product_type'] not in allowed_products:
        raise ValueError(
            f"Product type {quote_data['product_type']} not allowed "
            f"for this API key"
        )
    
    return create_quote(quote_data)
```

## Best Practices for Insurance System Decorators

1. **Layering Decorators**: Order matters when stacking decorators
   ```python
   @require_roles(Role.UNDERWRITER)  # Authentication first
   @validate_underwriting_limits()    # Then business rules
   @PolicyOperationLogger()          # Then logging
   @retry(max_attempts=3)           # Then retry logic
   @timeout(30)                     # Finally timeout
   def process_application(data):
       pass
   ```

2. **Error Handling**: Always preserve the original function's error semantics
   ```python
   def insurance_decorator(func):
       @wraps(func)
       def wrapper(*args, **kwargs):
           try:
               return func(*args, **kwargs)
           except PolicyException:
               # Re-raise domain exceptions
               raise
           except Exception as e:
               # Wrap other exceptions appropriately
               raise PolicyProcessingError(f"Failed to {func.__name__}: {e}")
       return wrapper
   ```

3. **Performance Considerations**: Be mindful of decorator overhead
   - Cache decorator instances when possible
   - Avoid heavy computations in decorators
   - Use lazy evaluation for expensive checks

4. **Testing Decorators**: Make decorators testable
   ```python
   def test_rate_limiter():
       limiter = RateLimiter(requests_per_second=2)
       
       @limiter
       def api_call():
           return "success"
       
       # Should succeed
       assert api_call() == "success"
       assert api_call() == "success"
       
       # Should fail
       with pytest.raises(Exception):
           api_call()
   ```

5. **Documentation**: Always document decorator behavior
   ```python
   def validate_coverage(max_amount: float):
       """
       Validates that requested coverage doesn't exceed maximum.
       
       Args:
           max_amount: Maximum allowed coverage amount
           
       Raises:
           ValidationError: If coverage exceeds maximum
           
       Example:
           @validate_coverage(1000000)
           def create_policy(coverage: float):
               pass
       """
   ```