# Python Performance Guardrails for Enterprise Insurance Systems

## Overview
Performance is critical in P&C insurance systems where real-time rating, quote generation, and claims processing directly impact business operations. This document defines mandatory performance patterns, async rules, memory limits, and profiling requirements.

## Core Performance Requirements

### 1. Response Time SLAs
- Quote Generation: < 3 seconds (95th percentile)
- Policy Lookup: < 500ms (95th percentile)
- Premium Calculation: < 1 second (95th percentile)
- Claims Submission: < 2 seconds (95th percentile)
- Batch Processing: 10,000 policies/hour minimum

### 2. Resource Limits
- Memory per request: Maximum 512MB
- CPU per request: Maximum 2 seconds computation time
- Database connections: Maximum 100 concurrent
- API calls: Maximum 1000/minute per service

## Async Programming Rules

### 1. Mandatory Async Patterns
```python
import asyncio
from typing import AsyncGenerator, TypeVar, Sequence
from asyncio import Semaphore, gather, create_task

T = TypeVar('T')

# WRONG: Blocking I/O in async context
async def get_policy_data(policy_id: str) -> PolicyData:
    # This blocks the event loop!
    response = requests.get(f"/api/policies/{policy_id}")
    return response.json()

# CORRECT: Proper async I/O
async def get_policy_data(policy_id: str) -> PolicyData:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"/api/policies/{policy_id}") as response:
            return await response.json()
```

### 2. Concurrent Operations
```python
class PolicyBatchProcessor:
    """Process policies concurrently with controlled parallelism"""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = Semaphore(max_concurrent)
        self.rate_limiter = RateLimiter(calls_per_second=50)
    
    async def process_policies(
        self,
        policy_ids: Sequence[str]
    ) -> list[ProcessResult]:
        """Process multiple policies concurrently"""
        
        async def process_with_limit(policy_id: str) -> ProcessResult:
            async with self.semaphore:  # Control concurrency
                await self.rate_limiter.acquire()  # Rate limiting
                try:
                    return await self._process_single_policy(policy_id)
                except Exception as e:
                    logger.error(f"Failed to process policy {policy_id}: {e}")
                    return ProcessResult(
                        policy_id=policy_id,
                        success=False,
                        error=str(e)
                    )
        
        # Process all policies concurrently
        tasks = [create_task(process_with_limit(pid)) for pid in policy_ids]
        return await gather(*tasks)
    
    async def _process_single_policy(self, policy_id: str) -> ProcessResult:
        """Process a single policy"""
        # Fetch data concurrently
        policy_task = self.get_policy_data(policy_id)
        claims_task = self.get_claims_data(policy_id)
        billing_task = self.get_billing_data(policy_id)
        
        policy, claims, billing = await gather(
            policy_task,
            claims_task,
            billing_task
        )
        
        # Process with the gathered data
        premium = await self.calculate_premium(policy, claims)
        
        return ProcessResult(
            policy_id=policy_id,
            success=True,
            premium=premium,
            claims_count=len(claims)
        )
```

### 3. Async Context Managers
```python
class DatabasePool:
    """Async database connection pool"""
    
    def __init__(self, dsn: str, min_size: int = 10, max_size: int = 100):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self._pool: Optional[asyncpg.Pool] = None
    
    async def __aenter__(self) -> 'DatabasePool':
        self._pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=10,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._pool:
            await self._pool.close()
    
    async def acquire(self) -> AsyncContextManager[Connection]:
        """Acquire a connection from the pool"""
        if not self._pool:
            raise RuntimeError("Pool not initialized")
        return self._pool.acquire()
    
    async def execute_many(
        self,
        query: str,
        args_list: list[tuple]
    ) -> None:
        """Execute query for multiple parameter sets efficiently"""
        async with self.acquire() as conn:
            # Use prepared statement for better performance
            stmt = await conn.prepare(query)
            await conn.executemany(stmt, args_list)
```

### 4. Async Generators
```python
async def stream_large_dataset(
    query: str,
    batch_size: int = 1000
) -> AsyncGenerator[list[PolicyData], None]:
    """Stream large datasets without loading all into memory"""
    
    async with DatabasePool() as pool:
        async with pool.acquire() as conn:
            # Use server-side cursor for memory efficiency
            async with conn.transaction():
                cursor = await conn.cursor(query)
                
                while True:
                    batch = await cursor.fetch(batch_size)
                    if not batch:
                        break
                    
                    yield [PolicyData.from_record(record) for record in batch]

# Usage with memory-efficient processing
async def process_all_policies():
    """Process all policies with controlled memory usage"""
    total_processed = 0
    
    async for policy_batch in stream_large_dataset(
        "SELECT * FROM policies WHERE status = 'ACTIVE'",
        batch_size=500
    ):
        # Process batch
        results = await process_policy_batch(policy_batch)
        total_processed += len(results)
        
        # Allow other tasks to run
        await asyncio.sleep(0)
    
    logger.info(f"Processed {total_processed} policies")
```

## Memory Management

### 1. Object Pooling
```python
from asyncio import Queue
from typing import Generic, TypeVar, Protocol

T = TypeVar('T')

class Poolable(Protocol):
    """Protocol for poolable objects"""
    def reset(self) -> None: ...

class ObjectPool(Generic[T]):
    """Generic object pool for expensive objects"""
    
    def __init__(
        self,
        factory: Callable[[], T],
        max_size: int = 100,
        pre_create: int = 10
    ):
        self.factory = factory
        self.max_size = max_size
        self._pool: Queue[T] = Queue(maxsize=max_size)
        self._created = 0
        
        # Pre-create objects
        for _ in range(min(pre_create, max_size)):
            obj = self.factory()
            self._pool.put_nowait(obj)
            self._created += 1
    
    async def acquire(self) -> T:
        """Acquire object from pool"""
        try:
            # Try to get from pool without blocking
            return self._pool.get_nowait()
        except QueueEmpty:
            # Create new if under limit
            if self._created < self.max_size:
                self._created += 1
                return self.factory()
            
            # Wait for available object
            return await self._pool.get()
    
    async def release(self, obj: T) -> None:
        """Return object to pool"""
        if hasattr(obj, 'reset'):
            obj.reset()
        
        try:
            self._pool.put_nowait(obj)
        except QueueFull:
            # Pool is full, let object be garbage collected
            pass

# Usage example
class PremiumCalculator:
    """Expensive calculator object suitable for pooling"""
    
    def __init__(self):
        # Load rating tables (expensive operation)
        self.rating_tables = self._load_rating_tables()
        self.cache = {}
    
    def reset(self) -> None:
        """Reset calculator state for reuse"""
        self.cache.clear()
    
    def calculate(self, policy_data: PolicyData) -> Decimal:
        """Calculate premium"""
        # Use loaded rating tables
        return self._apply_rates(policy_data)

# Create pool of calculators
calculator_pool = ObjectPool(
    factory=PremiumCalculator,
    max_size=50,
    pre_create=10
)

async def calculate_premium(policy_data: PolicyData) -> Decimal:
    """Calculate premium using pooled calculator"""
    calculator = await calculator_pool.acquire()
    try:
        return calculator.calculate(policy_data)
    finally:
        await calculator_pool.release(calculator)
```

### 2. Memory Profiling
```python
import tracemalloc
import psutil
import gc
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar('T')

class MemoryMonitor:
    """Monitor memory usage for operations"""
    
    def __init__(self, threshold_mb: float = 100):
        self.threshold_bytes = threshold_mb * 1024 * 1024
    
    def profile(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to profile memory usage"""
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Start tracing
            tracemalloc.start()
            gc.collect()  # Clean baseline
            
            start_memory = tracemalloc.get_traced_memory()[0]
            process = psutil.Process()
            start_rss = process.memory_info().rss
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                
                # Get memory stats
                current, peak = tracemalloc.get_traced_memory()
                end_rss = process.memory_info().rss
                
                memory_used = current - start_memory
                rss_increase = end_rss - start_rss
                
                # Log if threshold exceeded
                if memory_used > self.threshold_bytes:
                    logger.warning(
                        f"High memory usage in {func.__name__}",
                        extra={
                            "memory_used_mb": memory_used / 1024 / 1024,
                            "peak_mb": peak / 1024 / 1024,
                            "rss_increase_mb": rss_increase / 1024 / 1024
                        }
                    )
                    
                    # Get top memory allocations
                    snapshot = tracemalloc.take_snapshot()
                    top_stats = snapshot.statistics('lineno')[:10]
                    
                    for stat in top_stats:
                        logger.debug(f"Memory allocation: {stat}")
                
                return result
                
            finally:
                tracemalloc.stop()
        
        return wrapper

# Usage
memory_monitor = MemoryMonitor(threshold_mb=50)

@memory_monitor.profile
async def process_large_claim_batch(claims: list[ClaimData]) -> BatchResult:
    """Process large batch of claims with memory monitoring"""
    results = []
    
    # Process in chunks to control memory
    chunk_size = 100
    for i in range(0, len(claims), chunk_size):
        chunk = claims[i:i + chunk_size]
        chunk_results = await process_claim_chunk(chunk)
        results.extend(chunk_results)
        
        # Force garbage collection between chunks
        gc.collect()
    
    return BatchResult(results)
```

### 3. Memory Limits
```python
import resource
from contextlib import contextmanager

class MemoryLimiter:
    """Enforce memory limits for operations"""
    
    @staticmethod
    @contextmanager
    def limit(max_memory_mb: int):
        """Context manager to limit memory usage"""
        max_memory_bytes = max_memory_mb * 1024 * 1024
        
        # Get current limits
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        
        try:
            # Set new limit
            resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, hard))
            yield
        finally:
            # Restore original limit
            resource.setrlimit(resource.RLIMIT_AS, (soft, hard))

# Usage in memory-intensive operations
async def generate_actuarial_report(year: int) -> Report:
    """Generate report with memory limit"""
    
    with MemoryLimiter.limit(max_memory_mb=512):
        try:
            # Load and process large datasets
            claims_data = await load_claims_data(year)
            policy_data = await load_policy_data(year)
            
            # Process with streaming to stay within limit
            report = Report()
            
            async for claim_batch in stream_claims(claims_data):
                summary = await calculate_claim_summary(claim_batch)
                report.add_summary(summary)
                
                # Release memory
                del claim_batch
                gc.collect()
            
            return report
            
        except MemoryError:
            logger.error("Memory limit exceeded in report generation")
            raise InsuranceException(
                message="Report too large for available memory",
                error_code="MEM001",
                context={"year": year, "limit_mb": 512}
            )
```

## Performance Optimization Patterns

### 1. Caching Strategy
```python
from functools import lru_cache
import aiocache
from typing import Optional

class CacheConfig:
    """Cache configuration for different data types"""
    
    RATING_FACTORS = {
        "ttl": 3600,  # 1 hour
        "namespace": "rating",
        "serializer": "json"
    }
    
    POLICY_DATA = {
        "ttl": 300,  # 5 minutes
        "namespace": "policy",
        "serializer": "pickle"
    }
    
    STATIC_DATA = {
        "ttl": 86400,  # 24 hours
        "namespace": "static",
        "serializer": "json"
    }

class InsuranceCache:
    """Multi-tier caching system"""
    
    def __init__(self):
        # In-memory cache for hot data
        self.memory_cache = aiocache.Cache(aiocache.MEMORY)
        
        # Redis cache for distributed caching
        self.redis_cache = aiocache.Cache(
            aiocache.REDIS,
            endpoint="localhost",
            port=6379,
            pool_min_size=10,
            pool_max_size=100
        )
    
    async def get_or_compute(
        self,
        key: str,
        compute_func: Callable[[], Awaitable[T]],
        ttl: int = 300,
        cache_tier: str = "both"
    ) -> T:
        """Get from cache or compute if missing"""
        
        # Try memory cache first
        if cache_tier in ["memory", "both"]:
            value = await self.memory_cache.get(key)
            if value is not None:
                return value
        
        # Try Redis cache
        if cache_tier in ["redis", "both"]:
            value = await self.redis_cache.get(key)
            if value is not None:
                # Populate memory cache
                if cache_tier == "both":
                    await self.memory_cache.set(key, value, ttl=60)
                return value
        
        # Compute value
        value = await compute_func()
        
        # Cache in appropriate tiers
        if cache_tier in ["memory", "both"]:
            await self.memory_cache.set(key, value, ttl=ttl)
        if cache_tier in ["redis", "both"]:
            await self.redis_cache.set(key, value, ttl=ttl)
        
        return value

# Decorator for method caching
def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching method results"""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> T:
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"
            
            # Use instance cache if available
            if hasattr(self, 'cache'):
                return await self.cache.get_or_compute(
                    cache_key,
                    lambda: func(self, *args, **kwargs),
                    ttl=ttl
                )
            else:
                # Fallback to function execution
                return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator

class RatingEngine:
    """Rating engine with intelligent caching"""
    
    def __init__(self):
        self.cache = InsuranceCache()
    
    @cached(ttl=3600, key_prefix="rate")
    async def calculate_base_rate(
        self,
        territory: str,
        construction_type: str,
        protection_class: int
    ) -> Decimal:
        """Calculate base rate with caching"""
        # Expensive calculation
        rate_factors = await self._load_rate_factors(territory)
        construction_factor = rate_factors[construction_type]
        protection_factor = self._get_protection_factor(protection_class)
        
        return Decimal(str(construction_factor * protection_factor))
```

### 2. Batch Processing
```python
class BatchProcessor:
    """Efficient batch processing for insurance operations"""
    
    def __init__(
        self,
        batch_size: int = 1000,
        flush_interval: float = 5.0
    ):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._batch: list[Any] = []
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
    
    async def add(self, item: Any) -> None:
        """Add item to batch"""
        async with self._lock:
            self._batch.append(item)
            
            if len(self._batch) >= self.batch_size:
                await self._flush()
            elif not self._flush_task:
                # Schedule flush
                self._flush_task = asyncio.create_task(
                    self._scheduled_flush()
                )
    
    async def _scheduled_flush(self) -> None:
        """Flush batch after interval"""
        await asyncio.sleep(self.flush_interval)
        async with self._lock:
            if self._batch:
                await self._flush()
    
    async def _flush(self) -> None:
        """Process and clear batch"""
        if not self._batch:
            return
        
        batch = self._batch[:]
        self._batch.clear()
        
        # Cancel scheduled flush
        if self._flush_task:
            self._flush_task.cancel()
            self._flush_task = None
        
        # Process batch
        await self._process_batch(batch)
    
    async def _process_batch(self, batch: list[Any]) -> None:
        """Override in subclasses"""
        raise NotImplementedError

class PolicyUpdateBatcher(BatchProcessor):
    """Batch policy updates for efficiency"""
    
    async def _process_batch(self, batch: list[PolicyUpdate]) -> None:
        """Process batch of policy updates"""
        
        # Group by operation type
        updates_by_type = defaultdict(list)
        for update in batch:
            updates_by_type[update.operation].append(update)
        
        # Execute batched operations
        async with DatabasePool() as pool:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # Batch status updates
                    if status_updates := updates_by_type.get('status'):
                        await conn.executemany(
                            """
                            UPDATE policies 
                            SET status = $2, updated_at = NOW()
                            WHERE policy_number = $1
                            """,
                            [(u.policy_number, u.new_status) for u in status_updates]
                        )
                    
                    # Batch premium updates
                    if premium_updates := updates_by_type.get('premium'):
                        await conn.executemany(
                            """
                            UPDATE policies 
                            SET premium = $2, updated_at = NOW()
                            WHERE policy_number = $1
                            """,
                            [(u.policy_number, u.new_premium) for u in premium_updates]
                        )
        
        logger.info(f"Processed batch of {len(batch)} policy updates")
```

### 3. Query Optimization
```python
class QueryOptimizer:
    """SQL query optimization for insurance queries"""
    
    @staticmethod
    def create_indexes():
        """Create optimal indexes for common queries"""
        return [
            # Composite indexes for common query patterns
            """
            CREATE INDEX CONCURRENTLY idx_policies_status_effective 
            ON policies(status, effective_date) 
            WHERE status IN ('ACTIVE', 'PENDING');
            """,
            
            """
            CREATE INDEX CONCURRENTLY idx_claims_policy_status 
            ON claims(policy_number, status, loss_date DESC)
            INCLUDE (claim_amount);
            """,
            
            # Partial indexes for specific conditions
            """
            CREATE INDEX CONCURRENTLY idx_policies_renewal 
            ON policies(expiration_date, policy_number) 
            WHERE status = 'ACTIVE' 
            AND auto_renewal = true;
            """,
            
            # GIN index for JSONB search
            """
            CREATE INDEX CONCURRENTLY idx_policy_coverage_data 
            ON policies USING gin(coverage_data);
            """
        ]
    
    @staticmethod
    async def explain_analyze(
        conn: Connection,
        query: str,
        params: tuple
    ) -> dict[str, Any]:
        """Analyze query performance"""
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
        result = await conn.fetchval(explain_query, *params)
        
        plan = json.loads(result)[0]
        
        # Extract key metrics
        return {
            "execution_time": plan["Execution Time"],
            "planning_time": plan["Planning Time"],
            "total_cost": plan["Plan"]["Total Cost"],
            "rows_returned": plan["Plan"]["Actual Rows"],
            "buffers": plan["Plan"].get("Shared Hit Blocks", 0)
        }

class OptimizedPolicyRepository:
    """Repository with query optimization"""
    
    def __init__(self, db_pool: DatabasePool):
        self.db = db_pool
        self._prepared_statements: dict[str, str] = {}
    
    async def find_active_policies_by_expiration(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> list[Policy]:
        """Find policies expiring in date range (optimized)"""
        
        query = """
        SELECT 
            p.*,
            -- Pre-calculate commonly needed values
            EXTRACT(days FROM expiration_date - CURRENT_DATE) as days_until_expiry,
            EXISTS(
                SELECT 1 FROM claims c 
                WHERE c.policy_number = p.policy_number 
                AND c.status = 'OPEN'
            ) as has_open_claims
        FROM policies p
        WHERE p.status = 'ACTIVE'
        AND p.expiration_date BETWEEN $1 AND $2
        ORDER BY p.expiration_date, p.policy_number
        LIMIT $3
        """
        
        async with self.db.acquire() as conn:
            # Use prepared statement for better performance
            if query not in self._prepared_statements:
                self._prepared_statements[query] = await conn.prepare(query)
            
            stmt = self._prepared_statements[query]
            rows = await stmt.fetch(start_date, end_date, limit)
            
            return [Policy.from_row(row) for row in rows]
```

## Profiling and Monitoring

### 1. Performance Profiler
```python
import cProfile
import pstats
from line_profiler import LineProfiler
import time

class PerformanceProfiler:
    """Comprehensive performance profiling"""
    
    def __init__(self):
        self.profiles: dict[str, pstats.Stats] = {}
    
    def profile_function(self, func: Callable) -> Callable:
        """Decorator for function profiling"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            
            profiler.enable()
            start_time = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                profiler.disable()
                
                # Store profile
                stats = pstats.Stats(profiler)
                self.profiles[func.__name__] = stats
                
                # Log performance metrics
                logger.info(
                    f"Performance profile for {func.__name__}",
                    extra={
                        "execution_time": end_time - start_time,
                        "function_calls": stats.total_calls,
                        "primitive_calls": stats.prim_calls
                    }
                )
        
        return wrapper
    
    def get_hotspots(self, function_name: str, limit: int = 10) -> list[tuple]:
        """Get performance hotspots for function"""
        if function_name not in self.profiles:
            return []
        
        stats = self.profiles[function_name]
        stats.sort_stats('cumulative')
        
        # Extract top time consumers
        hotspots = []
        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            hotspots.append((
                f"{func[0]}:{func[1]}:{func[2]}",
                ct,  # Cumulative time
                nc   # Number of calls
            ))
        
        return sorted(hotspots, key=lambda x: x[1], reverse=True)[:limit]

# Line-level profiling for critical functions
def profile_critical_section(func: Callable) -> Callable:
    """Line-by-line profiling for critical sections"""
    profiler = LineProfiler()
    profiler.add_function(func)
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        profiler.enable()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            profiler.disable()
            # Print results to log
            profiler.print_stats()
    
    return wrapper
```

### 2. Real-time Monitoring
```python
from prometheus_client import Histogram, Counter, Gauge, Summary

# Define metrics
request_duration = Histogram(
    'insurance_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

active_connections = Gauge(
    'insurance_active_connections',
    'Number of active connections',
    ['connection_type']
)

memory_usage = Gauge(
    'insurance_memory_usage_bytes',
    'Memory usage in bytes',
    ['component']
)

cache_hit_rate = Summary(
    'insurance_cache_hit_rate',
    'Cache hit rate',
    ['cache_name']
)

class PerformanceMonitor:
    """Real-time performance monitoring"""
    
    def __init__(self):
        self.metrics_buffer: list[dict] = []
        self._flush_task = asyncio.create_task(self._flush_metrics())
    
    async def _flush_metrics(self):
        """Periodically flush metrics"""
        while True:
            await asyncio.sleep(10)  # Flush every 10 seconds
            
            if self.metrics_buffer:
                # Send to monitoring system
                await self._send_to_monitoring(self.metrics_buffer[:])
                self.metrics_buffer.clear()
    
    def track_request(self, method: str, endpoint: str):
        """Track request performance"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                
                # Track active connections
                active_connections.labels(connection_type="http").inc()
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    # Record duration
                    duration = time.perf_counter() - start_time
                    request_duration.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(duration)
                    
                    # Track memory
                    process = psutil.Process()
                    memory_usage.labels(
                        component="api"
                    ).set(process.memory_info().rss)
                    
                    active_connections.labels(connection_type="http").dec()
            
            return wrapper
        return decorator

# Usage
monitor = PerformanceMonitor()

@monitor.track_request("POST", "/api/policies/quote")
async def generate_quote(request: QuoteRequest) -> QuoteResponse:
    """Generate insurance quote with monitoring"""
    # Implementation
    pass
```

### 3. Performance Testing
```python
import asyncio
from locust import HttpUser, task, between

class InsuranceLoadTest(HttpUser):
    """Load testing for insurance APIs"""
    wait_time = between(1, 3)
    
    @task(weight=3)
    def get_policy(self):
        """Test policy retrieval"""
        policy_id = self.get_test_policy_id()
        with self.client.get(
            f"/api/policies/{policy_id}",
            catch_response=True
        ) as response:
            if response.elapsed.total_seconds() > 0.5:
                response.failure("Policy lookup exceeded 500ms SLA")
    
    @task(weight=2)
    def calculate_premium(self):
        """Test premium calculation"""
        with self.client.post(
            "/api/premiums/calculate",
            json=self.get_test_policy_data(),
            catch_response=True
        ) as response:
            if response.elapsed.total_seconds() > 1.0:
                response.failure("Premium calculation exceeded 1s SLA")

class PerformanceTestRunner:
    """Run performance tests and analyze results"""
    
    async def run_stress_test(
        self,
        target_function: Callable,
        concurrent_users: int = 100,
        duration_seconds: int = 60
    ) -> dict[str, Any]:
        """Run stress test on function"""
        
        results = {
            "successful_calls": 0,
            "failed_calls": 0,
            "response_times": [],
            "errors": []
        }
        
        async def user_simulation():
            """Simulate a single user"""
            end_time = time.time() + duration_seconds
            
            while time.time() < end_time:
                start = time.perf_counter()
                try:
                    await target_function()
                    elapsed = time.perf_counter() - start
                    results["successful_calls"] += 1
                    results["response_times"].append(elapsed)
                except Exception as e:
                    results["failed_calls"] += 1
                    results["errors"].append(str(e))
                
                # Random delay between requests
                await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Run concurrent users
        tasks = [
            asyncio.create_task(user_simulation())
            for _ in range(concurrent_users)
        ]
        
        await asyncio.gather(*tasks)
        
        # Calculate statistics
        if results["response_times"]:
            results["avg_response_time"] = statistics.mean(results["response_times"])
            results["p95_response_time"] = statistics.quantiles(
                results["response_times"],
                n=20
            )[18]  # 95th percentile
            results["p99_response_time"] = statistics.quantiles(
                results["response_times"],
                n=100
            )[98]  # 99th percentile
        
        return results
```

## Database Performance

### 1. Connection Pooling
```python
class OptimizedDatabasePool:
    """Optimized database connection pooling"""
    
    def __init__(self, dsn: str):
        self.dsn = dsn
        self._pool: Optional[asyncpg.Pool] = None
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize connection pool with optimal settings"""
        
        self._pool = await asyncpg.create_pool(
            self.dsn,
            # Pool size configuration
            min_size=10,
            max_size=100,
            
            # Connection configuration
            command_timeout=10,
            max_queries=50000,
            max_inactive_connection_lifetime=300,
            
            # Performance settings
            server_settings={
                'jit': 'off',  # Disable JIT for consistent performance
                'random_page_cost': '1.1',  # For SSD storage
                'effective_cache_size': '4GB',
                'shared_buffers': '1GB',
                'work_mem': '50MB',
                'maintenance_work_mem': '256MB'
            },
            
            # Initialize connection
            init=self._init_connection
        )
        
        # Start health check
        self._health_check_task = asyncio.create_task(self._health_check())
    
    async def _init_connection(self, conn: Connection):
        """Initialize each connection"""
        # Set connection parameters
        await conn.execute("SET statement_timeout = '30s'")
        await conn.execute("SET lock_timeout = '10s'")
        await conn.execute("SET idle_in_transaction_session_timeout = '60s'")
        
        # Prepare common statements
        await conn.prepare(
            "SELECT * FROM policies WHERE policy_number = $1"
        )
    
    async def _health_check(self):
        """Periodic health check of connections"""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            if self._pool:
                # Remove idle connections
                await self._pool.expire_connections()
                
                # Log pool statistics
                logger.info(
                    "Database pool health",
                    extra={
                        "size": self._pool.get_size(),
                        "free": self._pool.get_idle_size(),
                        "used": self._pool.get_size() - self._pool.get_idle_size()
                    }
                )
```

### 2. Query Batching
```python
class QueryBatcher:
    """Batch similar queries for efficiency"""
    
    def __init__(self, window_ms: int = 10):
        self.window_ms = window_ms
        self._batches: dict[str, list] = defaultdict(list)
        self._results: dict[str, Future] = {}
        self._flush_task: Optional[asyncio.Task] = None
    
    async def add_query(
        self,
        query_type: str,
        params: tuple,
        query_func: Callable
    ) -> Any:
        """Add query to batch and return future result"""
        
        query_id = f"{query_type}:{params}"
        future = asyncio.Future()
        
        self._batches[query_type].append((params, future))
        self._results[query_id] = future
        
        # Schedule batch execution
        if not self._flush_task:
            self._flush_task = asyncio.create_task(
                self._flush_batch(query_type, query_func)
            )
        
        return await future
    
    async def _flush_batch(
        self,
        query_type: str,
        query_func: Callable
    ):
        """Execute batched queries"""
        
        # Wait for batching window
        await asyncio.sleep(self.window_ms / 1000)
        
        batch = self._batches[query_type]
        if not batch:
            return
        
        self._batches[query_type] = []
        self._flush_task = None
        
        try:
            # Execute batch query
            all_params = [params for params, _ in batch]
            results = await query_func(all_params)
            
            # Distribute results
            for (params, future), result in zip(batch, results):
                future.set_result(result)
                
        except Exception as e:
            # Propagate error to all futures
            for _, future in batch:
                future.set_exception(e)
```

## Performance Best Practices

### 1. Async Best Practices
- Always use async/await for I/O operations
- Avoid blocking the event loop with synchronous calls
- Use asyncio.gather() for concurrent operations
- Implement proper connection pooling for all external services
- Use async context managers for resource management

### 2. Memory Best Practices
- Stream large datasets instead of loading into memory
- Use generators and async generators for data processing
- Implement object pooling for expensive objects
- Monitor memory usage and set appropriate limits
- Use weak references for caches when appropriate

### 3. CPU Best Practices
- Offload CPU-intensive tasks to process pool
- Use NumPy/Pandas for numerical computations
- Implement caching for expensive calculations
- Profile code to identify bottlenecks
- Consider Cython for performance-critical sections

### 4. Database Best Practices
- Use prepared statements for repeated queries
- Implement appropriate indexes for query patterns
- Batch similar operations together
- Use COPY for bulk inserts
- Monitor and optimize slow queries

### 5. Monitoring Best Practices
- Track all SLA metrics continuously
- Alert on performance degradation
- Maintain historical performance data
- Implement distributed tracing
- Regular load testing and capacity planning