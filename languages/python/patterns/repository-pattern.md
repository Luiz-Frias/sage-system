---
name: Repository Pattern
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# Repository Pattern for P&C Insurance Systems

## Overview

The Repository Pattern provides an abstraction layer between your business logic and data access layer, particularly useful for managing policy and claims data in P&C insurance systems. This pattern enables high-performance async operations while maintaining clean separation of concerns.

## Core Principles

1. **Abstraction**: Hide data access implementation details
2. **Testability**: Easy to mock for unit testing
3. **Flexibility**: Switch between different data sources without changing business logic
4. **Performance**: Leverage async/await for concurrent operations
5. **Type Safety**: Use type hints for better IDE support and runtime validation

## Basic Repository Interface

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime
import asyncio

# Type variable for generic entity
T = TypeVar('T')

class IRepository(ABC, Generic[T]):
    """Base repository interface for all entities."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Retrieve entity by its unique identifier."""
        pass
    
    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Retrieve all entities with pagination."""
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete an entity by id."""
        pass
    
    @abstractmethod
    async def exists(self, id: str) -> bool:
        """Check if entity exists."""
        pass
```

## Policy Repository Implementation

```python
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional, List, Dict, Any
import asyncpg
import json

class PolicyStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"

@dataclass
class Policy:
    """Policy entity model."""
    id: str
    policy_number: str
    insured_id: str
    product_code: str
    effective_date: date
    expiration_date: date
    premium: float
    status: PolicyStatus
    coverage_limits: Dict[str, float]
    deductibles: Dict[str, float]
    risk_factors: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

class PolicyRepository(IRepository[Policy]):
    """Async repository for policy management."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def get_by_id(self, id: str) -> Optional[Policy]:
        """Retrieve policy by ID with optimized query."""
        query = """
            SELECT id, policy_number, insured_id, product_code,
                   effective_date, expiration_date, premium, status,
                   coverage_limits, deductibles, risk_factors,
                   created_at, updated_at, version
            FROM policies
            WHERE id = $1 AND deleted_at IS NULL
        """
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, id)
            if row:
                return self._row_to_policy(row)
            return None
    
    async def get_by_policy_number(self, policy_number: str) -> Optional[Policy]:
        """Retrieve policy by policy number."""
        query = """
            SELECT * FROM policies
            WHERE policy_number = $1 AND deleted_at IS NULL
        """
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, policy_number)
            if row:
                return self._row_to_policy(row)
            return None
    
    async def get_active_policies_by_insured(
        self, insured_id: str
    ) -> List[Policy]:
        """Get all active policies for an insured."""
        query = """
            SELECT * FROM policies
            WHERE insured_id = $1 
                AND status = $2
                AND effective_date <= CURRENT_DATE
                AND expiration_date >= CURRENT_DATE
                AND deleted_at IS NULL
            ORDER BY effective_date DESC
        """
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, insured_id, PolicyStatus.ACTIVE.value)
            return [self._row_to_policy(row) for row in rows]
    
    async def get_policies_expiring_soon(
        self, days_ahead: int = 30
    ) -> List[Policy]:
        """Get policies expiring within specified days."""
        query = """
            SELECT * FROM policies
            WHERE status = $1
                AND expiration_date BETWEEN CURRENT_DATE 
                    AND CURRENT_DATE + INTERVAL '%s days'
                AND deleted_at IS NULL
            ORDER BY expiration_date ASC
        """
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                query % days_ahead, PolicyStatus.ACTIVE.value
            )
            return [self._row_to_policy(row) for row in rows]
    
    async def create(self, policy: Policy) -> Policy:
        """Create new policy with optimistic locking."""
        query = """
            INSERT INTO policies (
                id, policy_number, insured_id, product_code,
                effective_date, expiration_date, premium, status,
                coverage_limits, deductibles, risk_factors,
                created_at, updated_at, version
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
            )
            RETURNING *
        """
        
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    query,
                    policy.id,
                    policy.policy_number,
                    policy.insured_id,
                    policy.product_code,
                    policy.effective_date,
                    policy.expiration_date,
                    policy.premium,
                    policy.status.value,
                    json.dumps(policy.coverage_limits),
                    json.dumps(policy.deductibles),
                    json.dumps(policy.risk_factors),
                    policy.created_at,
                    policy.updated_at,
                    policy.version
                )
                return self._row_to_policy(row)
    
    async def update(self, policy: Policy) -> Policy:
        """Update policy with optimistic locking."""
        query = """
            UPDATE policies
            SET policy_number = $2,
                insured_id = $3,
                product_code = $4,
                effective_date = $5,
                expiration_date = $6,
                premium = $7,
                status = $8,
                coverage_limits = $9,
                deductibles = $10,
                risk_factors = $11,
                updated_at = $12,
                version = version + 1
            WHERE id = $1 AND version = $13 AND deleted_at IS NULL
            RETURNING *
        """
        
        policy.updated_at = datetime.utcnow()
        
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    query,
                    policy.id,
                    policy.policy_number,
                    policy.insured_id,
                    policy.product_code,
                    policy.effective_date,
                    policy.expiration_date,
                    policy.premium,
                    policy.status.value,
                    json.dumps(policy.coverage_limits),
                    json.dumps(policy.deductibles),
                    json.dumps(policy.risk_factors),
                    policy.updated_at,
                    policy.version
                )
                
                if not row:
                    raise ValueError(
                        f"Policy {policy.id} was modified by another process"
                    )
                
                return self._row_to_policy(row)
    
    async def batch_update_status(
        self, policy_ids: List[str], new_status: PolicyStatus
    ) -> int:
        """Batch update policy status for performance."""
        query = """
            UPDATE policies
            SET status = $1, updated_at = $2
            WHERE id = ANY($3) AND deleted_at IS NULL
        """
        
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                query, new_status.value, datetime.utcnow(), policy_ids
            )
            return int(result.split()[-1])
    
    async def get_all(
        self, limit: int = 100, offset: int = 0
    ) -> List[Policy]:
        """Get all policies with pagination."""
        query = """
            SELECT * FROM policies
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, limit, offset)
            return [self._row_to_policy(row) for row in rows]
    
    async def delete(self, id: str) -> bool:
        """Soft delete a policy."""
        query = """
            UPDATE policies
            SET deleted_at = $1
            WHERE id = $2 AND deleted_at IS NULL
        """
        
        async with self._pool.acquire() as conn:
            result = await conn.execute(query, datetime.utcnow(), id)
            return result.split()[-1] == "1"
    
    async def exists(self, id: str) -> bool:
        """Check if policy exists."""
        query = """
            SELECT 1 FROM policies
            WHERE id = $1 AND deleted_at IS NULL
            LIMIT 1
        """
        
        async with self._pool.acquire() as conn:
            result = await conn.fetchval(query, id)
            return result is not None
    
    def _row_to_policy(self, row: asyncpg.Record) -> Policy:
        """Convert database row to Policy entity."""
        return Policy(
            id=row['id'],
            policy_number=row['policy_number'],
            insured_id=row['insured_id'],
            product_code=row['product_code'],
            effective_date=row['effective_date'],
            expiration_date=row['expiration_date'],
            premium=float(row['premium']),
            status=PolicyStatus(row['status']),
            coverage_limits=json.loads(row['coverage_limits']),
            deductibles=json.loads(row['deductibles']),
            risk_factors=json.loads(row['risk_factors']),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            version=row['version']
        )
```

## Claims Repository with Advanced Queries

```python
@dataclass
class Claim:
    """Claim entity model."""
    id: str
    claim_number: str
    policy_id: str
    incident_date: date
    reported_date: date
    description: str
    claim_amount: float
    approved_amount: Optional[float]
    status: str
    adjuster_id: Optional[str]
    documents: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class ClaimRepository(IRepository[Claim]):
    """High-performance claim repository."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
    
    async def get_claims_by_policy(
        self, policy_id: str, status: Optional[str] = None
    ) -> List[Claim]:
        """Get claims for a policy with optional status filter."""
        query = """
            SELECT * FROM claims
            WHERE policy_id = $1
                AND ($2::text IS NULL OR status = $2)
                AND deleted_at IS NULL
            ORDER BY incident_date DESC
        """
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, policy_id, status)
            return [self._row_to_claim(row) for row in rows]
    
    async def get_high_value_claims(
        self, threshold: float, days_back: int = 90
    ) -> List[Claim]:
        """Get high-value claims for review."""
        query = """
            SELECT c.*, p.product_code, p.insured_id
            FROM claims c
            JOIN policies p ON c.policy_id = p.id
            WHERE c.claim_amount > $1
                AND c.incident_date >= CURRENT_DATE - INTERVAL '%s days'
                AND c.deleted_at IS NULL
            ORDER BY c.claim_amount DESC
        """
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query % days_back, threshold)
            return [self._row_to_claim(row) for row in rows]
    
    async def get_claims_summary_by_product(
        self, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Get claims summary grouped by product for analytics."""
        query = """
            SELECT 
                p.product_code,
                COUNT(c.id) as claim_count,
                SUM(c.claim_amount) as total_claimed,
                SUM(c.approved_amount) as total_approved,
                AVG(c.claim_amount) as avg_claim_amount,
                AVG(c.approved_amount) as avg_approved_amount,
                COUNT(CASE WHEN c.status = 'approved' THEN 1 END) as approved_count,
                COUNT(CASE WHEN c.status = 'denied' THEN 1 END) as denied_count
            FROM claims c
            JOIN policies p ON c.policy_id = p.id
            WHERE c.incident_date BETWEEN $1 AND $2
                AND c.deleted_at IS NULL
            GROUP BY p.product_code
            ORDER BY total_claimed DESC
        """
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, start_date, end_date)
            return [dict(row) for row in rows]
    
    async def batch_create_claims(
        self, claims: List[Claim]
    ) -> List[Claim]:
        """Batch create claims for performance."""
        query = """
            INSERT INTO claims (
                id, claim_number, policy_id, incident_date,
                reported_date, description, claim_amount,
                approved_amount, status, adjuster_id,
                documents, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING *
        """
        
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                created_claims = []
                
                # Use prepared statement for better performance
                stmt = await conn.prepare(query)
                
                for claim in claims:
                    row = await stmt.fetchrow(
                        claim.id,
                        claim.claim_number,
                        claim.policy_id,
                        claim.incident_date,
                        claim.reported_date,
                        claim.description,
                        claim.claim_amount,
                        claim.approved_amount,
                        claim.status,
                        claim.adjuster_id,
                        json.dumps(claim.documents),
                        claim.created_at,
                        claim.updated_at
                    )
                    created_claims.append(self._row_to_claim(row))
                
                return created_claims
    
    # Implement remaining abstract methods...
    
    def _row_to_claim(self, row: asyncpg.Record) -> Claim:
        """Convert database row to Claim entity."""
        return Claim(
            id=row['id'],
            claim_number=row['claim_number'],
            policy_id=row['policy_id'],
            incident_date=row['incident_date'],
            reported_date=row['reported_date'],
            description=row['description'],
            claim_amount=float(row['claim_amount']),
            approved_amount=float(row['approved_amount']) if row['approved_amount'] else None,
            status=row['status'],
            adjuster_id=row['adjuster_id'],
            documents=json.loads(row['documents']) if row['documents'] else [],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
```

## Unit of Work Pattern Integration

```python
class UnitOfWork:
    """Unit of Work pattern for transaction management."""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self._pool = connection_pool
        self._connection: Optional[asyncpg.Connection] = None
        self._transaction = None
        self.policies: Optional[PolicyRepository] = None
        self.claims: Optional[ClaimRepository] = None
    
    async def __aenter__(self):
        self._connection = await self._pool.acquire()
        self._transaction = self._connection.transaction()
        await self._transaction.start()
        
        # Initialize repositories with the connection
        self.policies = PolicyRepository(self._connection)
        self.claims = ClaimRepository(self._connection)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
        
        await self._pool.release(self._connection)
    
    async def commit(self):
        """Commit the transaction."""
        if self._transaction:
            await self._transaction.commit()
    
    async def rollback(self):
        """Rollback the transaction."""
        if self._transaction:
            await self._transaction.rollback()

# Usage example
async def process_policy_renewal(policy_id: str, pool: asyncpg.Pool):
    """Example of using Unit of Work for complex operations."""
    async with UnitOfWork(pool) as uow:
        # Get existing policy
        policy = await uow.policies.get_by_id(policy_id)
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
        
        # Create renewal policy
        renewal_policy = Policy(
            id=generate_id(),
            policy_number=f"{policy.policy_number}-RNW",
            insured_id=policy.insured_id,
            product_code=policy.product_code,
            effective_date=policy.expiration_date,
            expiration_date=policy.expiration_date.replace(
                year=policy.expiration_date.year + 1
            ),
            premium=policy.premium * 1.05,  # 5% increase
            status=PolicyStatus.ACTIVE,
            coverage_limits=policy.coverage_limits,
            deductibles=policy.deductibles,
            risk_factors=policy.risk_factors
        )
        
        # Create renewal policy
        await uow.policies.create(renewal_policy)
        
        # Update old policy status
        policy.status = PolicyStatus.EXPIRED
        await uow.policies.update(policy)
        
        # All operations committed atomically
        return renewal_policy
```

## Performance Optimization Strategies

### 1. Connection Pooling

```python
import asyncpg
from typing import Optional

class DatabaseConfig:
    """Database configuration with performance settings."""
    
    def __init__(
        self,
        dsn: str,
        min_connections: int = 10,
        max_connections: int = 100,
        max_inactive_connection_lifetime: float = 300.0,
        command_timeout: float = 60.0
    ):
        self.dsn = dsn
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.max_inactive_connection_lifetime = max_inactive_connection_lifetime
        self.command_timeout = command_timeout

async def create_connection_pool(config: DatabaseConfig) -> asyncpg.Pool:
    """Create optimized connection pool."""
    return await asyncpg.create_pool(
        config.dsn,
        min_size=config.min_connections,
        max_size=config.max_connections,
        max_inactive_connection_lifetime=config.max_inactive_connection_lifetime,
        command_timeout=config.command_timeout,
        # Performance optimizations
        server_settings={
            'jit': 'off',  # Disable JIT for consistent performance
            'search_path': 'public',
        },
        # Use prepared statements for better performance
        statement_cache_size=100,
        max_cached_statement_lifetime=300,
    )
```

### 2. Query Optimization

```python
class OptimizedPolicyRepository(PolicyRepository):
    """Repository with query optimizations."""
    
    async def get_policies_with_claims_summary(
        self, insured_id: str
    ) -> List[Dict[str, Any]]:
        """Get policies with claims summary using single query."""
        query = """
            WITH policy_claims AS (
                SELECT 
                    p.id,
                    p.policy_number,
                    p.product_code,
                    p.premium,
                    p.status,
                    COUNT(c.id) as claim_count,
                    COALESCE(SUM(c.claim_amount), 0) as total_claims,
                    COALESCE(MAX(c.incident_date), NULL) as last_claim_date
                FROM policies p
                LEFT JOIN claims c ON p.id = c.policy_id
                WHERE p.insured_id = $1 AND p.deleted_at IS NULL
                GROUP BY p.id, p.policy_number, p.product_code, 
                         p.premium, p.status
            )
            SELECT * FROM policy_claims
            ORDER BY policy_number
        """
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, insured_id)
            return [dict(row) for row in rows]
    
    async def bulk_load_policies(
        self, policy_ids: List[str]
    ) -> Dict[str, Policy]:
        """Bulk load policies for performance."""
        if not policy_ids:
            return {}
        
        query = """
            SELECT * FROM policies
            WHERE id = ANY($1) AND deleted_at IS NULL
        """
        
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, policy_ids)
            return {
                row['id']: self._row_to_policy(row)
                for row in rows
            }
```

### 3. Caching Layer

```python
import redis.asyncio as redis
import pickle
from typing import Optional, Callable, Any
import hashlib

class CachedRepository:
    """Repository decorator with Redis caching."""
    
    def __init__(
        self,
        repository: IRepository,
        redis_client: redis.Redis,
        default_ttl: int = 300
    ):
        self._repository = repository
        self._redis = redis_client
        self._default_ttl = default_ttl
    
    def _generate_cache_key(self, method: str, *args, **kwargs) -> str:
        """Generate cache key from method and arguments."""
        key_data = f"{method}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_by_id(self, id: str) -> Optional[Any]:
        """Get entity by ID with caching."""
        cache_key = self._generate_cache_key('get_by_id', id)
        
        # Try cache first
        cached = await self._redis.get(cache_key)
        if cached:
            return pickle.loads(cached)
        
        # Fetch from repository
        result = await self._repository.get_by_id(id)
        
        # Cache result
        if result:
            await self._redis.setex(
                cache_key,
                self._default_ttl,
                pickle.dumps(result)
            )
        
        return result
    
    async def invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        cursor = 0
        while True:
            cursor, keys = await self._redis.scan(
                cursor, match=pattern, count=100
            )
            if keys:
                await self._redis.delete(*keys)
            if cursor == 0:
                break
```

## Best Practices

1. **Always use connection pooling** for database connections
2. **Implement proper error handling** and retry logic
3. **Use transactions** for data consistency
4. **Leverage indexes** for frequently queried fields
5. **Implement caching** for read-heavy operations
6. **Use batch operations** when processing multiple entities
7. **Monitor query performance** and optimize slow queries
8. **Implement proper logging** for debugging and monitoring
9. **Use type hints** for better code maintainability
10. **Write comprehensive tests** for repository methods

## Testing Repositories

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_policy_repository_get_by_id():
    """Test get_by_id method."""
    # Mock connection pool
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    # Mock query result
    mock_row = {
        'id': 'test-id',
        'policy_number': 'POL-001',
        'insured_id': 'INS-001',
        'product_code': 'AUTO-COMP',
        'effective_date': date(2024, 1, 1),
        'expiration_date': date(2025, 1, 1),
        'premium': 1200.00,
        'status': 'active',
        'coverage_limits': '{}',
        'deductibles': '{}',
        'risk_factors': '{}',
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'version': 1
    }
    mock_conn.fetchrow.return_value = mock_row
    
    # Test repository
    repo = PolicyRepository(mock_pool)
    result = await repo.get_by_id('test-id')
    
    # Assertions
    assert result is not None
    assert result.id == 'test-id'
    assert result.policy_number == 'POL-001'
    mock_conn.fetchrow.assert_called_once()
```

## Common Pitfalls and Solutions

1. **N+1 Query Problem**: Use JOIN queries or batch loading
2. **Connection Leaks**: Always use context managers
3. **Large Result Sets**: Implement pagination and streaming
4. **Stale Cache**: Implement cache invalidation strategies
5. **Race Conditions**: Use optimistic locking with version fields