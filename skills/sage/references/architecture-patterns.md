# Architecture Patterns Reference

This document provides domain-agnostic architecture templates and patterns that SAGE
agents use when designing and building systems. Load this reference when making
architectural decisions or scaffolding system structure.

## Guiding Principles

1. **API-First**: Every capability exposed as an API before building consumers
2. **Cloud-Native**: Containerized, stateless, horizontally scalable
3. **Event-Driven**: Asynchronous communication, loose coupling
4. **Domain-Driven**: Aligned with business capabilities, not technical layers
5. **Security-by-Design**: Zero-trust, defense in depth
6. **Observability-First**: Structured logging, metrics, tracing from day one

## API Layering Pattern

Structure APIs in three tiers:

```
External Clients
       |
  [API Gateway]  — Authentication, rate limiting, routing
       |
  Experience APIs  — Channel-specific orchestration (web, mobile, partner)
       |
  Process APIs     — Business process orchestration (workflows, sagas)
       |
  System APIs      — System-level integration (CRUD, data access)
       |
  Core Services    — Business logic, domain services
       |
  Data Layer       — Databases, caches, event stores
```

### Experience APIs
- **Purpose**: Tailor responses for specific clients (web vs mobile vs partner)
- **Auth**: OAuth 2.0 + JWT
- **Protocol**: REST or GraphQL
- **Rate limiting**: Per-client limits

### Process APIs
- **Purpose**: Orchestrate multi-step business workflows
- **Versioning**: URI versioning (`/v1`, `/v2`)
- **Documentation**: OpenAPI 3.1
- **Idempotency**: Required for all mutating operations

### System APIs
- **Purpose**: Direct system integration, service-to-service
- **Auth**: mTLS for internal, API keys for external
- **Protocol**: REST or gRPC
- **Circuit breakers**: Required on all external calls

## Microservices Design

### Service Decomposition

Decompose by business capability, not by technical layer:

```yaml
# Good: Business-aligned services
services:
  - user-service        # User lifecycle management
  - order-service       # Order processing and fulfillment
  - payment-service     # Payment processing
  - notification-service # Multi-channel notifications

# Bad: Technical-layer services
services:
  - api-service         # Too broad
  - database-service    # Wrong abstraction
  - frontend-service    # Not a microservice concern
```

### Service Template

Every microservice should include:

```
{service-name}/
├── src/
│   ├── api/              # Route handlers, request/response DTOs
│   ├── domain/           # Business logic, entities, value objects
│   ├── infrastructure/   # Database, external APIs, messaging
│   └── config/           # Configuration, environment handling
├── tests/
│   ├── unit/             # Business logic tests
│   └── integration/      # API and database tests
├── Dockerfile
├── health-check endpoint (/health or /healthz)
└── OpenAPI spec (openapi.yaml)
```

### Database Per Service

Each service owns its data store:
- No direct database access across service boundaries
- Communication only through APIs or events
- Choose the right database for the workload (SQL, NoSQL, graph, etc.)
- Implement data consistency through sagas or eventual consistency

## Event-Driven Architecture

### Event Bus Design

```
Publishers → Event Bus (Kafka/RabbitMQ/EventBridge) → Subscribers

Topics organized by domain:
  - {domain}.events     (e.g., order.events, user.events)
  - {domain}.commands   (e.g., payment.commands)
  - {domain}.queries    (e.g., reporting.queries)
```

### Event Schema

```yaml
event:
  id: "uuid"
  type: "{Domain}{Action}"         # e.g., "OrderPlaced", "UserCreated"
  source: "{service-name}"
  timestamp: "ISO-8601"
  version: "1"
  data:
    # Event-specific payload
  metadata:
    correlation_id: "uuid"
    causation_id: "uuid"
    user_id: "uuid"
```

### Event Patterns

| Pattern | When to Use | Example |
|---------|-------------|---------|
| Event notification | Inform others something happened | `OrderPlaced` |
| Event-carried state transfer | Share data without API calls | `CustomerUpdated` with full customer data |
| Event sourcing | Need full audit trail | Financial transactions, compliance |
| CQRS | Read/write patterns differ significantly | Reporting vs. transactional |

## CQRS / Event Sourcing Pattern

### When to Use
- Audit trail is legally required
- Read and write patterns are fundamentally different
- Need to reconstruct historical state
- High read-to-write ratio

### Implementation

```
Commands → Command Handler → Event Store (append-only)
                                    |
                              Event Projector
                                    |
                              Read Models (materialized views, search indices)
                                    |
Queries → Query Handler → Read Store
```

### Event Store Design
- Append-only — events are immutable
- Ordered by aggregate ID and sequence number
- Snapshotting for performance (every N events)
- Retention policy based on compliance requirements

## Data Architecture Patterns

### Layered Data Architecture

```
Bronze (Raw)     → Ingest raw data as-is from sources
Silver (Cleaned) → Validate, deduplicate, normalize
Gold (Curated)   → Business-ready aggregations and models
```

### Data Quality Dimensions

| Dimension | Target | Measurement |
|-----------|--------|-------------|
| Completeness | > 98% | Non-null required fields / Total records |
| Accuracy | > 99% | Validated records / Total records |
| Consistency | > 99% | Cross-reference matches / Total checks |
| Timeliness | < 5 min | Ingestion to availability lag |
| Validity | > 99% | Schema-valid records / Total records |
| Uniqueness | > 99.9% | Unique records / Total records |

### Caching Strategy

Three-level caching:

| Level | Technology | TTL | Use Case |
|-------|-----------|-----|----------|
| L1: Application | In-memory (local) | 1-5 min | Hot data, session state |
| L2: Distributed | Redis/Memcached | 5-60 min | Shared state, API responses |
| L3: CDN/Edge | CloudFront/Fastly | 1-24 hr | Static assets, public content |

Cache invalidation strategies:
- **TTL-based**: Simple, eventual consistency
- **Event-driven**: Invalidate on write events
- **Cache-aside**: Application manages cache explicitly

## Security Architecture

### Zero-Trust Model

```
Every request must:
1. Be authenticated (who are you?)
2. Be authorized (are you allowed?)
3. Be encrypted (can anyone eavesdrop?)
4. Be audited (can we prove what happened?)
```

### Security Layers

| Layer | Controls |
|-------|----------|
| Edge | DDoS protection, WAF, geo-blocking, rate limiting |
| API | OAuth 2.0, API key management, JWT validation, CORS |
| Service | mTLS, service mesh policies, RBAC, secrets management |
| Data | Encryption at rest (AES-256), in transit (TLS 1.3), field-level encryption, masking |

### Authentication Patterns

| Pattern | Use Case |
|---------|----------|
| JWT + Refresh tokens | Web/mobile apps with session management |
| API keys + HMAC | Service-to-service, partner integrations |
| mTLS | Internal service mesh communication |
| OAuth 2.0 / OIDC | Third-party integrations, SSO |

## Deployment Patterns

### Container Strategy

```yaml
deployment:
  platform: Kubernetes
  patterns:
    - rolling_update    # Default: gradual replacement
    - blue_green        # Zero-downtime: swap environments
    - canary            # Progressive: 5% → 25% → 50% → 100%

  pod_sizing:
    web_tier:     { cpu: "500m-2000m", memory: "512Mi-2Gi", replicas: "3-10" }
    api_tier:     { cpu: "1-4 cores",  memory: "1-4Gi",     replicas: "5-20" }
    worker_tier:  { cpu: "2-8 cores",  memory: "2-8Gi",     replicas: "2-5" }
```

### CI/CD Pipeline Stages

```
Code Commit
  → Build (compile, lint)
  → Unit Tests
  → Integration Tests
  → Security Scan (SAST, dependency audit)
  → Container Build
  → Push to Registry
  → Deploy to Staging
  → E2E Tests
  → Deploy to Production (with rollback capability)
```

## Observability Stack

### Three Pillars

| Pillar | Tool Category | Purpose |
|--------|--------------|---------|
| Metrics | Prometheus + Grafana | Quantitative system health |
| Logging | ELK / Loki | Qualitative event records |
| Tracing | Jaeger / Zipkin | Request flow across services |

### Key SLIs (Service Level Indicators)

| Indicator | Target | Measurement |
|-----------|--------|-------------|
| Availability | 99.9% | Successful requests / Total requests |
| Latency (p50) | < 200ms | Request duration |
| Latency (p95) | < 500ms | Request duration |
| Latency (p99) | < 1000ms | Request duration |
| Error rate | < 0.1% | 5xx errors / Total requests |
| Throughput | > 1000 rps | Requests per second |

### Health Check Endpoint

Every service must expose `/health` or `/healthz`:

```json
{
  "status": "healthy",
  "version": "1.2.3",
  "uptime": "12h34m",
  "checks": {
    "database": "connected",
    "cache": "connected",
    "event_bus": "connected"
  }
}
```

## Integration Patterns

| Pattern | When to Use | Characteristics |
|---------|-------------|-----------------|
| Request-Response (REST) | Synchronous data retrieval | Simple, well-understood |
| Pub-Sub (Events) | One-to-many notification | Decoupled, scalable |
| Message Queue | Task distribution | Reliable, ordered |
| gRPC | High-performance service-to-service | Fast, typed, streaming |
| Webhook | External system callbacks | Event-driven, push-based |
| Batch/ETL | Large data transfers | Scheduled, high-throughput |
| CDC (Change Data Capture) | Database synchronization | Real-time, low-overhead |

## Disaster Recovery

| Tier | RTO | RPO | Strategy |
|------|-----|-----|----------|
| Critical | 1 hour | 15 minutes | Active-active multi-region |
| Important | 4 hours | 1 hour | Active-passive with hot standby |
| Standard | 24 hours | 4 hours | Backup and restore |

Recovery essentials:
- Continuous database replication
- Hourly file/config snapshots
- Git-versioned infrastructure (IaC)
- Quarterly DR testing with documented runbooks
