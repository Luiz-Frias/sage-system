---
name: Async Patterns
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# High-Performance Async/Await Patterns for P&C Insurance Systems

## Overview

Asynchronous programming is crucial for building high-performance P&C insurance systems that handle multiple concurrent operations like policy lookups, risk calculations, and claims processing. This guide covers advanced async patterns optimized for insurance workloads.

## Core Concepts

### Why Async for Insurance Systems?

1. **Concurrent API Calls**: Multiple external services (credit checks, DMV records, weather data)
2. **Database Operations**: Parallel queries for policy and claims data
3. **Real-time Processing**: Instant quotes and policy decisions
4. **Resource Efficiency**: Handle thousands of concurrent requests
5. **Scalability**: Better CPU and I/O utilization

## Basic Async Patterns

### 1. Async Function Basics

```python
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import aiohttp

# Basic async function
async def calculate_premium(
    policy_data: Dict[str, Any]
) -> float:
    """Calculate insurance premium asynchronously."""
    # Simulate async computation
    await asyncio.sleep(0.1)
    
    base_premium = policy_data.get('base_rate', 1000)
    risk_factor = policy_data.get('risk_score', 1.0)
    
    return base_premium * risk_factor

# Calling async functions
async def main():
    policy = {'base_rate': 1200, 'risk_score': 1.15}
    premium = await calculate_premium(policy)
    print(f"Premium: ${premium:,.2f}")

# Run the async function
asyncio.run(main())
```

### 2. Concurrent Execution

```python
async def fetch_driver_record(driver_id: str) -> Dict[str, Any]:
    """Fetch driver record from DMV API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.dmv.example/drivers/{driver_id}"
        ) as response:
            return await response.json()

async def fetch_credit_score(ssn: str) -> int:
    """Fetch credit score from credit bureau."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.creditbureau.example/score",
            json={"ssn": ssn}
        ) as response:
            data = await response.json()
            return data['score']

async def fetch_claims_history(driver_id: str) -> List[Dict[str, Any]]:
    """Fetch claims history from internal database."""
    # Simulate database query
    await asyncio.sleep(0.1)
    return [{"date": "2023-01-01", "amount": 5000}]

async def process_auto_application(
    driver_id: str, ssn: str
) -> Dict[str, Any]:
    """Process auto insurance application with concurrent data fetching."""
    # Run all fetches concurrently
    driver_record, credit_score, claims_history = await asyncio.gather(
        fetch_driver_record(driver_id),
        fetch_credit_score(ssn),
        fetch_claims_history(driver_id),
        return_exceptions=True  # Don't fail if one request fails
    )
    
    # Handle potential exceptions
    if isinstance(driver_record, Exception):
        driver_record = {"status": "error", "violations": []}
    
    if isinstance(credit_score, Exception):
        credit_score = 650  # Default score
    
    if isinstance(claims_history, Exception):
        claims_history = []
    
    return {
        "driver_record": driver_record,
        "credit_score": credit_score,
        "claims_history": claims_history,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Advanced Async Patterns

### 1. Async Context Managers

```python
import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncIterator

class DatabasePool:
    """Async database connection pool manager."""
    
    def __init__(self, dsn: str, min_size: int = 10, max_size: int = 100):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self._pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize the connection pool."""
        self._pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=60,
            max_cached_statement_lifetime=300
        )
    
    async def close(self):
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
    
    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        """Acquire a connection from the pool."""
        if not self._pool:
            raise RuntimeError("Pool not initialized")
        
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)
    
    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        """Acquire a connection and start a transaction."""
        async with self.acquire() as conn:
            async with conn.transaction():
                yield conn

# Usage example
async def update_policy_premium(
    pool: DatabasePool, policy_id: str, new_premium: float
):
    """Update policy premium in a transaction."""
    async with pool.transaction() as conn:
        # Update premium
        await conn.execute(
            "UPDATE policies SET premium = $1 WHERE id = $2",
            new_premium, policy_id
        )
        
        # Log the change
        await conn.execute(
            """
            INSERT INTO premium_history (policy_id, old_premium, new_premium, changed_at)
            SELECT id, premium, $1, $2 FROM policies WHERE id = $3
            """,
            new_premium, datetime.utcnow(), policy_id
        )
```

### 2. Async Generators and Streaming

```python
from typing import AsyncGenerator
import csv
import aiofiles

async def stream_large_claims_file(
    file_path: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream large claims CSV file without loading into memory."""
    async with aiofiles.open(file_path, mode='r') as file:
        # Read header
        header = await file.readline()
        columns = header.strip().split(',')
        
        # Stream rows
        async for line in file:
            values = line.strip().split(',')
            claim = dict(zip(columns, values))
            
            # Convert types
            claim['amount'] = float(claim.get('amount', 0))
            claim['incident_date'] = datetime.fromisoformat(
                claim['incident_date']
            )
            
            yield claim

async def process_claims_batch(
    claims: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Process a batch of claims."""
    total_amount = sum(claim['amount'] for claim in claims)
    avg_amount = total_amount / len(claims) if claims else 0
    
    return {
        'count': len(claims),
        'total_amount': total_amount,
        'average_amount': avg_amount
    }

async def analyze_claims_stream(file_path: str, batch_size: int = 1000):
    """Analyze claims in batches for memory efficiency."""
    batch = []
    results = []
    
    async for claim in stream_large_claims_file(file_path):
        batch.append(claim)
        
        if len(batch) >= batch_size:
            # Process batch asynchronously
            result = await process_claims_batch(batch)
            results.append(result)
            batch = []
    
    # Process final batch
    if batch:
        result = await process_claims_batch(batch)
        results.append(result)
    
    # Aggregate results
    total_claims = sum(r['count'] for r in results)
    total_amount = sum(r['total_amount'] for r in results)
    
    return {
        'total_claims': total_claims,
        'total_amount': total_amount,
        'average_amount': total_amount / total_claims if total_claims else 0
    }
```

### 3. Async Queue Pattern

```python
import asyncio
from asyncio import Queue
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

class AsyncTaskQueue:
    """High-performance async task queue for insurance operations."""
    
    def __init__(
        self,
        worker_count: int = 10,
        queue_size: int = 1000
    ):
        self.worker_count = worker_count
        self.queue: Queue = Queue(maxsize=queue_size)
        self.workers: List[asyncio.Task] = []
        self._running = False
        self._results = {}
    
    async def start(self):
        """Start worker tasks."""
        self._running = True
        for i in range(self.worker_count):
            worker = asyncio.create_task(
                self._worker(f"worker-{i}")
            )
            self.workers.append(worker)
    
    async def stop(self):
        """Stop all workers gracefully."""
        self._running = False
        
        # Wait for queue to be empty
        await self.queue.join()
        
        # Cancel workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for cancellation
        await asyncio.gather(*self.workers, return_exceptions=True)
    
    async def _worker(self, name: str):
        """Worker coroutine that processes tasks from queue."""
        logger.info(f"{name} started")
        
        while self._running:
            try:
                # Get task from queue with timeout
                task_id, func, args, kwargs = await asyncio.wait_for(
                    self.queue.get(), timeout=1.0
                )
                
                try:
                    # Execute task
                    result = await func(*args, **kwargs)
                    self._results[task_id] = ('success', result)
                except Exception as e:
                    logger.error(f"{name} error processing {task_id}: {e}")
                    self._results[task_id] = ('error', str(e))
                finally:
                    self.queue.task_done()
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
        
        logger.info(f"{name} stopped")
    
    async def submit(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ):
        """Submit a task to the queue."""
        await self.queue.put((task_id, func, args, kwargs))
    
    async def get_result(self, task_id: str) -> Any:
        """Get result of a completed task."""
        while task_id not in self._results:
            await asyncio.sleep(0.1)
        
        status, result = self._results.pop(task_id)
        if status == 'error':
            raise Exception(result)
        return result

# Usage example
async def calculate_risk_score(
    policy_data: Dict[str, Any]
) -> float:
    """Calculate risk score for a policy."""
    # Simulate complex calculation
    await asyncio.sleep(0.5)
    
    base_score = 1.0
    if policy_data.get('age', 0) < 25:
        base_score *= 1.5
    if policy_data.get('violations', 0) > 0:
        base_score *= 1.2
    
    return base_score

async def batch_risk_calculation(policies: List[Dict[str, Any]]):
    """Calculate risk scores for multiple policies concurrently."""
    queue = AsyncTaskQueue(worker_count=20)
    await queue.start()
    
    try:
        # Submit all tasks
        task_ids = []
        for i, policy in enumerate(policies):
            task_id = f"risk-{i}"
            await queue.submit(
                task_id,
                calculate_risk_score,
                policy
            )
            task_ids.append(task_id)
        
        # Collect results
        results = []
        for task_id in task_ids:
            result = await queue.get_result(task_id)
            results.append(result)
        
        return results
    finally:
        await queue.stop()
```

### 4. Async Semaphore for Rate Limiting

```python
class RateLimitedAPIClient:
    """API client with async rate limiting."""
    
    def __init__(
        self,
        base_url: str,
        max_concurrent_requests: int = 10,
        requests_per_second: int = 100
    ):
        self.base_url = base_url
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.rate_limiter = AsyncRateLimiter(requests_per_second)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make rate-limited API request."""
        async with self.semaphore:
            await self.rate_limiter.acquire()
            
            url = f"{self.base_url}{endpoint}"
            async with self.session.request(
                method, url, **kwargs
            ) as response:
                response.raise_for_status()
                return await response.json()

class AsyncRateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: int):
        self.rate = rate
        self.tokens = rate
        self.updated_at = asyncio.get_event_loop().time()
        self.lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1):
        """Acquire tokens, waiting if necessary."""
        async with self.lock:
            while self.tokens < tokens:
                now = asyncio.get_event_loop().time()
                elapsed = now - self.updated_at
                
                # Add new tokens based on elapsed time
                self.tokens = min(
                    self.rate,
                    self.tokens + elapsed * self.rate
                )
                self.updated_at = now
                
                if self.tokens < tokens:
                    # Wait for more tokens
                    sleep_time = (tokens - self.tokens) / self.rate
                    await asyncio.sleep(sleep_time)
            
            self.tokens -= tokens

# Usage example
async def fetch_multiple_quotes(
    client: RateLimitedAPIClient,
    quote_requests: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Fetch multiple insurance quotes with rate limiting."""
    tasks = [
        client.request('POST', '/quotes', json=request)
        for request in quote_requests
    ]
    
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### 5. Async Circuit Breaker Pattern

```python
from enum import Enum
from datetime import datetime, timedelta
import asyncio
from typing import Callable, Any, Optional

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class AsyncCircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception(
                        "Circuit breaker is OPEN"
                    )
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except self.expected_exception as e:
            await self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset the circuit."""
        return (
            self.last_failure_time and
            datetime.utcnow() - self.last_failure_time > 
            timedelta(seconds=self.recovery_timeout)
        )
    
    async def _on_success(self):
        """Handle successful call."""
        async with self._lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
    
    async def _on_failure(self):
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

# Usage example
class ExternalRatingService:
    """External rating service with circuit breaker."""
    
    def __init__(self):
        self.circuit_breaker = AsyncCircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=aiohttp.ClientError
        )
    
    async def get_rating(
        self, policy_data: Dict[str, Any]
    ) -> float:
        """Get rating from external service."""
        return await self.circuit_breaker.call(
            self._fetch_rating,
            policy_data
        )
    
    async def _fetch_rating(
        self, policy_data: Dict[str, Any]
    ) -> float:
        """Actual API call to rating service."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.rating.example/calculate',
                json=policy_data,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data['rating']
```

## Performance Optimization Techniques

### 1. Connection Pooling

```python
class OptimizedAPIClient:
    """API client with connection pooling and keep-alive."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._connector = None
        self._session = None
    
    async def __aenter__(self):
        # Create connector with connection pooling
        self._connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=30,  # Per-host limit
            ttl_dns_cache=300,  # DNS cache timeout
            enable_cleanup_closed=True
        )
        
        # Create session with optimized timeouts
        timeout = aiohttp.ClientTimeout(
            total=30,
            connect=5,
            sock_connect=5,
            sock_read=10
        )
        
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
            headers={
                'Connection': 'keep-alive',
                'Keep-Alive': 'timeout=600, max=1000'
            }
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
        if self._connector:
            await self._connector.close()
```

### 2. Batch Processing

```python
from typing import List, Tuple
import asyncio

class BatchProcessor:
    """Process items in optimized batches."""
    
    @staticmethod
    async def process_in_batches(
        items: List[Any],
        process_func: Callable[[List[Any]], Any],
        batch_size: int = 100,
        max_concurrent_batches: int = 10
    ) -> List[Any]:
        """Process items in concurrent batches."""
        # Create batches
        batches = [
            items[i:i + batch_size]
            for i in range(0, len(items), batch_size)
        ]
        
        # Process batches with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent_batches)
        
        async def process_batch(batch: List[Any]) -> Any:
            async with semaphore:
                return await process_func(batch)
        
        # Process all batches
        results = await asyncio.gather(
            *[process_batch(batch) for batch in batches]
        )
        
        # Flatten results
        return [item for batch_result in results for item in batch_result]

# Usage example
async def validate_policies_batch(
    policies: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Validate a batch of policies."""
    validated = []
    
    for policy in policies:
        # Simulate validation
        await asyncio.sleep(0.01)
        policy['validated'] = True
        policy['validation_timestamp'] = datetime.utcnow()
        validated.append(policy)
    
    return validated

async def validate_all_policies(
    policies: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Validate all policies using batch processing."""
    return await BatchProcessor.process_in_batches(
        policies,
        validate_policies_batch,
        batch_size=50,
        max_concurrent_batches=5
    )
```

### 3. Async Caching

```python
import aiocache
from aiocache import cached
import hashlib
import json

class AsyncCache:
    """Async caching with Redis backend."""
    
    def __init__(self, redis_url: str):
        self.cache = aiocache.Cache(
            aiocache.Cache.REDIS,
            endpoint=redis_url.split(':')[0],
            port=int(redis_url.split(':')[1]),
            namespace="insurance"
        )
    
    def key_builder(
        self,
        func_name: str,
        *args,
        **kwargs
    ) -> str:
        """Build cache key from function arguments."""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def get_or_compute(
        self,
        key: str,
        compute_func: Callable,
        ttl: int = 300
    ) -> Any:
        """Get from cache or compute and store."""
        # Try to get from cache
        value = await self.cache.get(key)
        if value is not None:
            return value
        
        # Compute value
        value = await compute_func()
        
        # Store in cache
        await self.cache.set(key, value, ttl=ttl)
        
        return value

# Decorator for caching
def async_cached(ttl: int = 300):
    """Decorator for async function caching."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cache_key = hashlib.md5(
                cache_key.encode()
            ).hexdigest()
            
            # Check cache
            cache = aiocache.Cache(aiocache.Cache.MEMORY)
            value = await cache.get(cache_key)
            
            if value is None:
                # Compute and cache
                value = await func(*args, **kwargs)
                await cache.set(cache_key, value, ttl=ttl)
            
            return value
        return wrapper
    return decorator

# Usage
@async_cached(ttl=600)
async def calculate_territory_rate(
    zip_code: str
) -> float:
    """Calculate insurance rate for territory."""
    # Expensive calculation
    await asyncio.sleep(1)
    return 1.0 + (int(zip_code) % 50) / 100
```

## Error Handling and Resilience

```python
import backoff
from typing import TypeVar, Type

T = TypeVar('T')

class AsyncRetry:
    """Configurable async retry mechanism."""
    
    @staticmethod
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        max_time=300
    )
    async def with_exponential_backoff(
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Retry with exponential backoff."""
        return await func(*args, **kwargs)
    
    @staticmethod
    async def with_fallback(
        primary_func: Callable[..., T],
        fallback_func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Try primary function, fall back on error."""
        try:
            return await primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(
                f"Primary function failed: {e}, using fallback"
            )
            return await fallback_func(*args, **kwargs)

# Usage example
async def get_quote_from_primary(
    policy_data: Dict[str, Any]
) -> float:
    """Get quote from primary rating engine."""
    # API call to primary service
    pass

async def get_quote_from_fallback(
    policy_data: Dict[str, Any]
) -> float:
    """Get quote from fallback rating engine."""
    # Simplified local calculation
    base_rate = 1000
    age_factor = 1.0 if policy_data['age'] > 25 else 1.5
    return base_rate * age_factor

async def get_insurance_quote(
    policy_data: Dict[str, Any]
) -> float:
    """Get quote with fallback."""
    return await AsyncRetry.with_fallback(
        get_quote_from_primary,
        get_quote_from_fallback,
        policy_data
    )
```

## Testing Async Code

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_concurrent_api_calls():
    """Test concurrent API calls."""
    # Mock API responses
    async def mock_api_call(endpoint: str) -> Dict[str, Any]:
        await asyncio.sleep(0.1)  # Simulate network delay
        return {"endpoint": endpoint, "status": "success"}
    
    # Make concurrent calls
    endpoints = ["/policy", "/claims", "/billing"]
    results = await asyncio.gather(
        *[mock_api_call(ep) for ep in endpoints]
    )
    
    # Verify results
    assert len(results) == 3
    assert all(r["status"] == "success" for r in results)

@pytest.mark.asyncio
async def test_rate_limiter():
    """Test async rate limiter."""
    rate_limiter = AsyncRateLimiter(rate=10)  # 10 per second
    
    start_time = asyncio.get_event_loop().time()
    
    # Try to acquire 20 tokens (should take ~1 second)
    for _ in range(20):
        await rate_limiter.acquire()
    
    elapsed = asyncio.get_event_loop().time() - start_time
    
    # Should take approximately 1 second
    assert 0.9 < elapsed < 1.2

@pytest.fixture
def mock_database_pool():
    """Mock database pool for testing."""
    pool = AsyncMock()
    conn = AsyncMock()
    
    # Setup connection acquisition
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None
    
    return pool, conn
```

## Best Practices

1. **Always use `async with` for resources** (connections, sessions)
2. **Prefer `asyncio.gather()` for concurrent operations**
3. **Implement proper timeout handling** for all external calls
4. **Use connection pooling** for databases and HTTP clients
5. **Batch operations** when possible to reduce overhead
6. **Implement circuit breakers** for external dependencies
7. **Add comprehensive logging** for debugging async flows
8. **Test with realistic concurrency** levels
9. **Monitor event loop lag** in production
10. **Use async-friendly libraries** (aiohttp, asyncpg, motor)

## Common Pitfalls

1. **Blocking the event loop**: Never use blocking I/O in async functions
2. **Not handling exceptions**: Always handle exceptions in concurrent tasks
3. **Resource leaks**: Ensure proper cleanup of connections and sessions
4. **Overloading external services**: Implement rate limiting
5. **Ignoring backpressure**: Monitor queue sizes and add limits