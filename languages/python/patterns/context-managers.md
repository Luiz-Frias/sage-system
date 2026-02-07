---
name: Context Managers
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# Context Managers for P&C Insurance Systems

## Overview

Context managers are essential for managing resources like database connections, file handles, API sessions, and transactions in insurance systems. They ensure proper resource cleanup and provide elegant error handling, critical for maintaining data integrity in policy and claims processing.

## Core Concepts

### Why Context Managers in Insurance?

1. **Transaction Safety**: Ensure database transactions commit or rollback properly
2. **Resource Management**: Manage connections to external services (credit bureaus, DMV, etc.)
3. **Audit Trails**: Automatically log entry/exit of critical operations
4. **Lock Management**: Handle distributed locks for concurrent policy updates
5. **State Management**: Maintain consistent state during complex operations

## Basic Context Manager Patterns

### 1. Class-Based Context Manager

```python
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime
import psycopg2
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Context manager for database connections with automatic retry."""
    
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        max_retries: int = 3
    ):
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.max_retries = max_retries
        self.connection: Optional[psycopg2.connection] = None
        self.cursor: Optional[psycopg2.cursor] = None
    
    def __enter__(self):
        """Establish database connection with retry logic."""
        retries = 0
        while retries < self.max_retries:
            try:
                self.connection = psycopg2.connect(**self.connection_params)
                self.cursor = self.connection.cursor()
                logger.info(f"Database connection established")
                return self
            except psycopg2.OperationalError as e:
                retries += 1
                if retries >= self.max_retries:
                    logger.error(f"Failed to connect after {self.max_retries} attempts")
                    raise
                logger.warning(f"Connection attempt {retries} failed, retrying...")
                time.sleep(2 ** retries)  # Exponential backoff
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up database resources."""
        if self.cursor:
            self.cursor.close()
        
        if self.connection:
            if exc_type:
                # Rollback on exception
                self.connection.rollback()
                logger.error(f"Transaction rolled back due to: {exc_val}")
            else:
                # Commit on success
                self.connection.commit()
                logger.info("Transaction committed successfully")
            
            self.connection.close()
            logger.info("Database connection closed")
        
        # Return False to propagate exceptions
        return False
    
    def execute(self, query: str, params: tuple = None) -> Any:
        """Execute a query with the managed cursor."""
        if not self.cursor:
            raise RuntimeError("No active database connection")
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

# Usage example
def update_policy_premium(policy_id: str, new_premium: float):
    """Update policy premium with automatic transaction management."""
    with DatabaseConnection(
        host="localhost",
        port=5432,
        database="insurance",
        user="app_user",
        password="secure_password"
    ) as db:
        # Get current premium for audit
        current = db.execute(
            "SELECT premium FROM policies WHERE id = %s",
            (policy_id,)
        )
        
        if not current:
            raise ValueError(f"Policy {policy_id} not found")
        
        old_premium = current[0][0]
        
        # Update premium
        db.execute(
            "UPDATE policies SET premium = %s, updated_at = %s WHERE id = %s",
            (new_premium, datetime.utcnow(), policy_id)
        )
        
        # Create audit record
        db.execute(
            """
            INSERT INTO premium_audit (policy_id, old_premium, new_premium, changed_at)
            VALUES (%s, %s, %s, %s)
            """,
            (policy_id, old_premium, new_premium, datetime.utcnow())
        )
        
        logger.info(f"Premium updated for policy {policy_id}: {old_premium} -> {new_premium}")
```

### 2. Function-Based Context Manager

```python
from contextlib import contextmanager
import redis
import json
import uuid
from typing import Optional, Any

@contextmanager
def distributed_lock(
    redis_client: redis.Redis,
    resource: str,
    timeout: int = 30,
    blocking_timeout: int = 10
):
    """
    Distributed lock for preventing concurrent modifications.
    Used for policy updates, claim processing, etc.
    """
    lock_id = str(uuid.uuid4())
    lock_key = f"lock:{resource}"
    acquired = False
    
    try:
        # Try to acquire lock
        acquired = redis_client.set(
            lock_key,
            lock_id,
            nx=True,  # Only set if not exists
            ex=timeout  # Expire after timeout seconds
        )
        
        if not acquired:
            # Wait for lock with timeout
            start_time = time.time()
            while time.time() - start_time < blocking_timeout:
                if redis_client.set(lock_key, lock_id, nx=True, ex=timeout):
                    acquired = True
                    break
                time.sleep(0.1)
        
        if not acquired:
            raise TimeoutError(f"Could not acquire lock for {resource}")
        
        logger.info(f"Acquired lock for {resource} with id {lock_id}")
        yield lock_id
        
    finally:
        if acquired:
            # Release lock only if we own it
            current_lock = redis_client.get(lock_key)
            if current_lock and current_lock.decode() == lock_id:
                redis_client.delete(lock_key)
                logger.info(f"Released lock for {resource}")

# Usage example
def process_claim_payment(claim_id: str, amount: float):
    """Process claim payment with distributed locking."""
    redis_client = redis.Redis(host='localhost', port=6379)
    
    with distributed_lock(redis_client, f"claim:{claim_id}", timeout=60):
        # Check if claim already processed
        claim_status = get_claim_status(claim_id)
        if claim_status == 'paid':
            raise ValueError(f"Claim {claim_id} already processed")
        
        # Process payment
        payment_id = initiate_payment(claim_id, amount)
        update_claim_status(claim_id, 'paid', payment_id)
        
        logger.info(f"Claim {claim_id} payment processed: ${amount}")
```

### 3. Async Context Managers

```python
import asyncio
import asyncpg
from typing import Optional, AsyncIterator
from contextlib import asynccontextmanager

class AsyncDatabasePool:
    """Async context manager for database connection pooling."""
    
    def __init__(
        self,
        dsn: str,
        min_size: int = 10,
        max_size: int = 100
    ):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None
    
    async def __aenter__(self):
        """Create and return connection pool."""
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            max_inactive_connection_lifetime=300.0,
            command_timeout=60.0
        )
        logger.info(f"Database pool created with {self.min_size}-{self.max_size} connections")
        return self.pool
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
        return False

@asynccontextmanager
async def async_transaction(
    pool: asyncpg.Pool
) -> AsyncIterator[asyncpg.Connection]:
    """Async context manager for database transactions."""
    connection = await pool.acquire()
    transaction = connection.transaction()
    
    try:
        await transaction.start()
        logger.debug("Transaction started")
        yield connection
        await transaction.commit()
        logger.debug("Transaction committed")
    except Exception as e:
        await transaction.rollback()
        logger.error(f"Transaction rolled back: {e}")
        raise
    finally:
        await pool.release(connection)

# Usage example
async def transfer_policy_ownership(
    policy_id: str,
    old_owner_id: str,
    new_owner_id: str
):
    """Transfer policy ownership with transaction safety."""
    async with AsyncDatabasePool(
        "postgresql://user:password@localhost/insurance"
    ) as pool:
        async with async_transaction(pool) as conn:
            # Verify policy exists and is owned by old owner
            policy = await conn.fetchrow(
                "SELECT * FROM policies WHERE id = $1 AND owner_id = $2",
                policy_id, old_owner_id
            )
            
            if not policy:
                raise ValueError("Policy not found or not owned by specified owner")
            
            # Update policy ownership
            await conn.execute(
                """
                UPDATE policies 
                SET owner_id = $1, updated_at = $2 
                WHERE id = $3
                """,
                new_owner_id, datetime.utcnow(), policy_id
            )
            
            # Create ownership transfer record
            await conn.execute(
                """
                INSERT INTO ownership_transfers 
                (policy_id, from_owner_id, to_owner_id, transferred_at)
                VALUES ($1, $2, $3, $4)
                """,
                policy_id, old_owner_id, new_owner_id, datetime.utcnow()
            )
            
            logger.info(f"Policy {policy_id} transferred from {old_owner_id} to {new_owner_id}")
```

## Advanced Context Manager Patterns

### 1. Nested Context Managers

```python
from contextlib import ExitStack, contextmanager
import tempfile
import shutil
import os

@contextmanager
def policy_document_processor(
    policy_id: str,
    s3_bucket: str
):
    """
    Process policy documents with multiple resource management.
    Handles temp directories, S3 connections, and database transactions.
    """
    with ExitStack() as stack:
        # Create temporary directory
        temp_dir = stack.enter_context(
            tempfile.TemporaryDirectory(prefix=f"policy_{policy_id}_")
        )
        logger.info(f"Created temp directory: {temp_dir}")
        
        # Open database connection
        db_conn = stack.enter_context(
            DatabaseConnection(
                host="localhost",
                port=5432,
                database="insurance",
                user="app_user",
                password="secure_password"
            )
        )
        
        # Open S3 client
        s3_client = stack.enter_context(
            S3Client(bucket=s3_bucket)
        )
        
        # Create processor object with all resources
        processor = PolicyDocumentProcessor(
            policy_id=policy_id,
            temp_dir=temp_dir,
            db_conn=db_conn,
            s3_client=s3_client
        )
        
        yield processor
        
        # Cleanup happens automatically in reverse order

class PolicyDocumentProcessor:
    """Processes policy documents with managed resources."""
    
    def __init__(self, policy_id: str, temp_dir: str, db_conn, s3_client):
        self.policy_id = policy_id
        self.temp_dir = temp_dir
        self.db_conn = db_conn
        self.s3_client = s3_client
    
    def generate_policy_pdf(self) -> str:
        """Generate PDF document for policy."""
        # Get policy data from database
        policy_data = self.db_conn.execute(
            "SELECT * FROM policies WHERE id = %s",
            (self.policy_id,)
        )
        
        # Generate PDF in temp directory
        pdf_path = os.path.join(self.temp_dir, f"policy_{self.policy_id}.pdf")
        # ... PDF generation logic ...
        
        # Upload to S3
        s3_key = f"policies/{self.policy_id}/policy_document.pdf"
        self.s3_client.upload_file(pdf_path, s3_key)
        
        # Update database with document location
        self.db_conn.execute(
            "UPDATE policies SET document_url = %s WHERE id = %s",
            (f"s3://{self.s3_client.bucket}/{s3_key}", self.policy_id)
        )
        
        return s3_key

# Usage
def generate_policy_documents(policy_id: str):
    """Generate all documents for a policy."""
    with policy_document_processor(policy_id, "insurance-documents") as processor:
        pdf_key = processor.generate_policy_pdf()
        logger.info(f"Generated policy document: {pdf_key}")
```

### 2. Reentrant Context Manager

```python
import threading
from contextlib import contextmanager

class ReentrantLock:
    """Reentrant lock context manager for recursive operations."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._count = 0
    
    def __enter__(self):
        self._lock.acquire()
        self._count += 1
        logger.debug(f"Lock acquired, count: {self._count}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._count -= 1
        logger.debug(f"Lock releasing, count: {self._count}")
        self._lock.release()
        return False

class PolicyCalculationEngine:
    """Thread-safe policy calculation engine."""
    
    def __init__(self):
        self._lock = ReentrantLock()
        self._cache = {}
    
    def calculate_premium(self, policy_data: Dict[str, Any]) -> float:
        """Calculate premium with thread safety."""
        with self._lock:
            cache_key = self._generate_cache_key(policy_data)
            
            if cache_key in self._cache:
                logger.debug(f"Premium cache hit for {cache_key}")
                return self._cache[cache_key]
            
            # Calculate base premium
            base_premium = self._calculate_base_premium(policy_data)
            
            # Apply modifiers (may recursively call calculate_premium)
            final_premium = self._apply_modifiers(base_premium, policy_data)
            
            self._cache[cache_key] = final_premium
            return final_premium
    
    def _calculate_base_premium(self, policy_data: Dict[str, Any]) -> float:
        """Calculate base premium."""
        with self._lock:  # Reentrant lock allows this
            # Complex calculation logic
            return policy_data.get('base_rate', 1000.0)
    
    def _apply_modifiers(self, base: float, policy_data: Dict[str, Any]) -> float:
        """Apply premium modifiers."""
        with self._lock:  # Can be called recursively
            modifiers = policy_data.get('modifiers', [])
            result = base
            
            for modifier in modifiers:
                if modifier['type'] == 'discount':
                    result *= (1 - modifier['value'])
                elif modifier['type'] == 'surcharge':
                    result *= (1 + modifier['value'])
            
            return result
    
    def _generate_cache_key(self, policy_data: Dict[str, Any]) -> str:
        """Generate cache key from policy data."""
        import hashlib
        import json
        
        # Sort keys for consistent hashing
        sorted_data = json.dumps(policy_data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()
```

### 3. Parameterized Context Manager

```python
from enum import Enum
from typing import Optional, Callable
import functools

class AuditLevel(Enum):
    NONE = 0
    BASIC = 1
    DETAILED = 2
    FULL = 3

class AuditContext:
    """Context manager for auditing insurance operations."""
    
    def __init__(
        self,
        operation: str,
        user_id: str,
        level: AuditLevel = AuditLevel.BASIC,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.operation = operation
        self.user_id = user_id
        self.level = level
        self.metadata = metadata or {}
        self.start_time = None
        self.audit_id = str(uuid.uuid4())
    
    def __enter__(self):
        """Start audit logging."""
        self.start_time = time.time()
        
        if self.level >= AuditLevel.BASIC:
            audit_entry = {
                'audit_id': self.audit_id,
                'operation': self.operation,
                'user_id': self.user_id,
                'started_at': datetime.utcnow().isoformat(),
                'metadata': self.metadata
            }
            
            # Log to audit system
            logger.info(f"Audit started: {json.dumps(audit_entry)}")
            
            if self.level >= AuditLevel.DETAILED:
                # Store in database
                self._store_audit_entry(audit_entry)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete audit logging."""
        duration = time.time() - self.start_time
        
        if self.level >= AuditLevel.BASIC:
            audit_completion = {
                'audit_id': self.audit_id,
                'operation': self.operation,
                'user_id': self.user_id,
                'completed_at': datetime.utcnow().isoformat(),
                'duration_seconds': duration,
                'success': exc_type is None,
                'error': str(exc_val) if exc_val else None
            }
            
            if self.level >= AuditLevel.FULL:
                # Include full stack trace
                import traceback
                audit_completion['stack_trace'] = traceback.format_exc() if exc_type else None
            
            logger.info(f"Audit completed: {json.dumps(audit_completion)}")
            
            if self.level >= AuditLevel.DETAILED:
                self._update_audit_entry(audit_completion)
        
        return False  # Don't suppress exceptions
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata during operation."""
        self.metadata[key] = value
        
        if self.level >= AuditLevel.DETAILED:
            logger.debug(f"Audit {self.audit_id} metadata updated: {key}={value}")
    
    def _store_audit_entry(self, entry: Dict[str, Any]):
        """Store audit entry in database."""
        # Implementation depends on your audit storage
        pass
    
    def _update_audit_entry(self, completion: Dict[str, Any]):
        """Update audit entry with completion details."""
        # Implementation depends on your audit storage
        pass

# Decorator for automatic auditing
def audited(
    operation: str,
    level: AuditLevel = AuditLevel.BASIC
):
    """Decorator to automatically audit function calls."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user_id from first argument if available
            user_id = kwargs.get('user_id', 'system')
            
            with AuditContext(
                operation=f"{operation}.{func.__name__}",
                user_id=user_id,
                level=level,
                metadata={
                    'function': func.__name__,
                    'args': str(args)[:100],  # Truncate for security
                    'kwargs_keys': list(kwargs.keys())
                }
            ) as audit:
                result = func(*args, **kwargs)
                
                # Add result metadata if detailed auditing
                if level >= AuditLevel.DETAILED:
                    audit.add_metadata('result_type', type(result).__name__)
                
                return result
        
        return wrapper
    return decorator

# Usage
@audited("policy.underwriting", level=AuditLevel.FULL)
def underwrite_policy(
    policy_data: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """Underwrite a new policy with full auditing."""
    # Underwriting logic here
    risk_score = calculate_risk_score(policy_data)
    premium = calculate_premium_from_risk(risk_score)
    
    return {
        'approved': risk_score < 0.8,
        'risk_score': risk_score,
        'premium': premium
    }
```

### 4. Resource Pool Context Manager

```python
from queue import Queue, Empty
import threading

class ResourcePool:
    """Generic resource pool context manager."""
    
    def __init__(
        self,
        resource_factory: Callable[[], Any],
        min_size: int = 5,
        max_size: int = 20
    ):
        self.resource_factory = resource_factory
        self.min_size = min_size
        self.max_size = max_size
        self.pool = Queue(maxsize=max_size)
        self.size = 0
        self.lock = threading.Lock()
        
        # Pre-populate with minimum resources
        for _ in range(min_size):
            resource = resource_factory()
            self.pool.put(resource)
            self.size += 1
    
    @contextmanager
    def acquire(self, timeout: float = 30.0):
        """Acquire a resource from the pool."""
        resource = None
        created = False
        
        try:
            # Try to get from pool
            try:
                resource = self.pool.get(block=True, timeout=timeout)
            except Empty:
                # Create new resource if under max size
                with self.lock:
                    if self.size < self.max_size:
                        resource = self.resource_factory()
                        self.size += 1
                        created = True
                    else:
                        raise TimeoutError("Resource pool exhausted")
            
            yield resource
            
        finally:
            if resource is not None:
                if created and self.size > self.min_size:
                    # Don't return to pool if over min size
                    with self.lock:
                        self.size -= 1
                    # Clean up resource
                    if hasattr(resource, 'close'):
                        resource.close()
                else:
                    # Return to pool
                    self.pool.put(resource)

# API Client Pool
class APIClientPool:
    """Pool of API clients for external services."""
    
    def __init__(self, base_url: str, api_key: str):
        self.pool = ResourcePool(
            resource_factory=lambda: self._create_client(base_url, api_key),
            min_size=5,
            max_size=50
        )
    
    def _create_client(self, base_url: str, api_key: str):
        """Create a new API client."""
        import requests
        session = requests.Session()
        session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        session.base_url = base_url
        return session
    
    def get_quote(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get insurance quote using pooled client."""
        with self.pool.acquire() as client:
            response = client.post(
                f"{client.base_url}/quotes",
                json=policy_data
            )
            response.raise_for_status()
            return response.json()

# Usage
quote_api = APIClientPool(
    base_url="https://api.insurance-quotes.com",
    api_key="your-api-key"
)

# Multiple concurrent requests use pooled connections
quote = quote_api.get_quote({
    'coverage_type': 'comprehensive',
    'vehicle_year': 2020,
    'driver_age': 35
})
```

## Integration with Insurance Workflows

### 1. Policy Lifecycle Management

```python
class PolicyLifecycleManager:
    """Manages policy lifecycle with proper resource handling."""
    
    @contextmanager
    def policy_creation_context(
        self,
        policy_data: Dict[str, Any],
        user_id: str
    ):
        """Context for creating a new policy."""
        policy_id = str(uuid.uuid4())
        
        with ExitStack() as stack:
            # Start audit trail
            audit = stack.enter_context(
                AuditContext(
                    operation="policy.create",
                    user_id=user_id,
                    level=AuditLevel.FULL,
                    metadata={'policy_id': policy_id}
                )
            )
            
            # Acquire distributed lock
            redis_client = redis.Redis()
            lock = stack.enter_context(
                distributed_lock(
                    redis_client,
                    f"policy:create:{policy_data.get('vehicle_vin')}",
                    timeout=300
                )
            )
            
            # Open database transaction
            db = stack.enter_context(
                DatabaseConnection(
                    host="localhost",
                    port=5432,
                    database="insurance",
                    user="app_user",
                    password="secure_password"
                )
            )
            
            # Create context object
            context = PolicyCreationContext(
                policy_id=policy_id,
                policy_data=policy_data,
                user_id=user_id,
                audit=audit,
                db=db
            )
            
            yield context
            
            # If we get here, everything succeeded
            audit.add_metadata('policy_created', True)
            audit.add_metadata('policy_number', context.policy_number)

class PolicyCreationContext:
    """Context object for policy creation."""
    
    def __init__(self, policy_id, policy_data, user_id, audit, db):
        self.policy_id = policy_id
        self.policy_data = policy_data
        self.user_id = user_id
        self.audit = audit
        self.db = db
        self.policy_number = None
    
    def create_policy(self) -> str:
        """Create the policy in the database."""
        self.policy_number = self._generate_policy_number()
        
        self.db.execute(
            """
            INSERT INTO policies (
                id, policy_number, insured_id, product_code,
                effective_date, expiration_date, premium,
                status, coverage_data, created_by, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                self.policy_id,
                self.policy_number,
                self.policy_data['insured_id'],
                self.policy_data['product_code'],
                self.policy_data['effective_date'],
                self.policy_data['expiration_date'],
                self.policy_data['premium'],
                'active',
                json.dumps(self.policy_data['coverage']),
                self.user_id,
                datetime.utcnow()
            )
        )
        
        self.audit.add_metadata('policy_number', self.policy_number)
        return self.policy_number
    
    def _generate_policy_number(self) -> str:
        """Generate unique policy number."""
        # Implementation specific to your business rules
        return f"POL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

# Usage
def create_new_policy(policy_data: Dict[str, Any], user_id: str) -> str:
    """Create a new insurance policy."""
    lifecycle_manager = PolicyLifecycleManager()
    
    with lifecycle_manager.policy_creation_context(
        policy_data, user_id
    ) as context:
        # Validate policy data
        validate_policy_data(policy_data)
        
        # Check for duplicate policies
        check_duplicate_policy(context.db, policy_data)
        
        # Calculate premium
        premium = calculate_premium(policy_data)
        context.policy_data['premium'] = premium
        
        # Create policy
        policy_number = context.create_policy()
        
        # Generate initial documents
        generate_policy_documents(context.policy_id)
        
        # Send confirmation
        send_policy_confirmation(policy_number, policy_data['insured_email'])
        
        return policy_number
```

### 2. Claims Processing Context

```python
class ClaimsProcessingContext:
    """Context manager for claims processing workflow."""
    
    def __init__(self, claim_id: str):
        self.claim_id = claim_id
        self.resources = {}
    
    async def __aenter__(self):
        """Set up claims processing resources."""
        # Initialize all required resources
        self.resources['db_pool'] = await AsyncDatabasePool(
            "postgresql://user:password@localhost/insurance"
        ).__aenter__()
        
        # Get claim details
        async with async_transaction(self.resources['db_pool']) as conn:
            claim = await conn.fetchrow(
                "SELECT * FROM claims WHERE id = $1",
                self.claim_id
            )
            if not claim:
                raise ValueError(f"Claim {self.claim_id} not found")
            
            self.resources['claim'] = dict(claim)
            self.resources['policy_id'] = claim['policy_id']
        
        # Set up external service clients
        self.resources['fraud_detector'] = FraudDetectionClient()
        self.resources['damage_assessor'] = DamageAssessmentClient()
        self.resources['payment_processor'] = PaymentProcessorClient()
        
        logger.info(f"Claims processing context initialized for {self.claim_id}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources."""
        # Close all resources in reverse order
        if 'db_pool' in self.resources:
            await self.resources['db_pool'].__aexit__(exc_type, exc_val, exc_tb)
        
        logger.info(f"Claims processing context cleaned up for {self.claim_id}")
        return False
    
    async def assess_claim(self) -> Dict[str, Any]:
        """Run full claim assessment."""
        # Run assessments in parallel
        fraud_check, damage_assessment = await asyncio.gather(
            self.resources['fraud_detector'].check_claim(self.resources['claim']),
            self.resources['damage_assessor'].assess_damage(self.resources['claim'])
        )
        
        return {
            'fraud_risk': fraud_check['risk_score'],
            'estimated_damage': damage_assessment['amount'],
            'recommended_payout': self._calculate_payout(
                damage_assessment['amount'],
                self.resources['claim']['deductible']
            )
        }
    
    def _calculate_payout(self, damage_amount: float, deductible: float) -> float:
        """Calculate recommended payout amount."""
        return max(0, damage_amount - deductible)

# Usage
async def process_claim(claim_id: str) -> Dict[str, Any]:
    """Process an insurance claim."""
    async with ClaimsProcessingContext(claim_id) as context:
        # Assess the claim
        assessment = await context.assess_claim()
        
        # Update claim status
        async with async_transaction(context.resources['db_pool']) as conn:
            await conn.execute(
                """
                UPDATE claims 
                SET status = $1, 
                    fraud_score = $2,
                    assessed_amount = $3,
                    approved_amount = $4,
                    assessed_at = $5
                WHERE id = $6
                """,
                'assessed',
                assessment['fraud_risk'],
                assessment['estimated_damage'],
                assessment['recommended_payout'],
                datetime.utcnow(),
                claim_id
            )
        
        return assessment
```

## Best Practices

1. **Always use context managers** for resources that need cleanup
2. **Implement proper error handling** in `__exit__` methods
3. **Use `ExitStack`** for managing multiple context managers
4. **Make context managers reusable** when appropriate
5. **Log entry and exit** for debugging and auditing
6. **Handle both sync and async** patterns based on requirements
7. **Test exception scenarios** to ensure proper cleanup
8. **Document resource requirements** clearly
9. **Use type hints** for better IDE support
10. **Consider thread safety** for shared resources

## Common Pitfalls and Solutions

1. **Resource Leaks**: Always implement `__exit__` properly
2. **Exception Suppression**: Return `False` from `__exit__` to propagate
3. **Deadlocks**: Be careful with nested locks
4. **Async Mixing**: Don't mix sync and async contexts carelessly
5. **State Corruption**: Ensure atomic operations in transactions