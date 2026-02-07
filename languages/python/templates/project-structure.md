---
name: Project Structure
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# Python Insurance API Project Structure

This document outlines the recommended project structure for Python-based insurance APIs using FastAPI, with a focus on maintainability, scalability, and domain-driven design.

## Directory Layout

```
insurance-api/
├── app/                              # Main application package
│   ├── __init__.py
│   ├── main.py                       # FastAPI app entry point
│   ├── config.py                     # Application configuration
│   ├── dependencies.py               # Dependency injection setup
│   │
│   ├── api/                          # API layer
│   │   ├── __init__.py
│   │   ├── v1/                       # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/            # API endpoints
│   │   │   │   ├── __init__.py
│   │   │   │   ├── policies.py      # Policy management
│   │   │   │   ├── quotes.py        # Quote generation
│   │   │   │   ├── claims.py        # Claims processing
│   │   │   │   ├── customers.py     # Customer management
│   │   │   │   ├── products.py      # Product catalog
│   │   │   │   ├── documents.py     # Document handling
│   │   │   │   ├── payments.py      # Payment processing
│   │   │   │   ├── reports.py       # Reporting endpoints
│   │   │   │   ├── webhooks.py      # Webhook receivers
│   │   │   │   └── health.py        # Health checks
│   │   │   └── dependencies.py      # API-specific deps
│   │   ├── middleware/               # Custom middleware
│   │   │   ├── __init__.py
│   │   │   ├── auth.py              # Authentication
│   │   │   ├── cors.py              # CORS handling
│   │   │   ├── logging.py           # Request logging
│   │   │   ├── rate_limit.py        # Rate limiting
│   │   │   └── error_handler.py     # Error handling
│   │   └── websockets/               # WebSocket handlers
│   │       ├── __init__.py
│   │       └── notifications.py      # Real-time updates
│   │
│   ├── core/                         # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py                 # Core settings
│   │   ├── security.py               # Security utilities
│   │   ├── exceptions.py             # Custom exceptions
│   │   ├── logging.py                # Logging setup
│   │   ├── events.py                 # Event handlers
│   │   ├── constants.py              # App constants
│   │   └── enums.py                  # Enumerations
│   │
│   ├── models/                       # Domain models
│   │   ├── __init__.py
│   │   ├── base.py                   # Base model classes
│   │   ├── policy.py                 # Policy models
│   │   ├── quote.py                  # Quote models
│   │   ├── claim.py                  # Claim models
│   │   ├── customer.py               # Customer models
│   │   ├── product.py                # Product models
│   │   ├── coverage.py               # Coverage models
│   │   ├── premium.py                # Premium models
│   │   ├── risk.py                   # Risk models
│   │   ├── document.py               # Document models
│   │   ├── payment.py                # Payment models
│   │   └── audit.py                  # Audit trail models
│   │
│   ├── schemas/                      # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── base.py                   # Base schemas
│   │   ├── requests/                 # Request schemas
│   │   │   ├── __init__.py
│   │   │   ├── policy.py
│   │   │   ├── quote.py
│   │   │   ├── claim.py
│   │   │   └── customer.py
│   │   ├── responses/                # Response schemas
│   │   │   ├── __init__.py
│   │   │   ├── policy.py
│   │   │   ├── quote.py
│   │   │   ├── claim.py
│   │   │   ├── error.py
│   │   │   └── pagination.py
│   │   └── internal/                 # Internal schemas
│   │       ├── __init__.py
│   │       └── events.py
│   │
│   ├── services/                     # Business logic
│   │   ├── __init__.py
│   │   ├── base.py                   # Base service class
│   │   ├── policy_engine.py          # Policy decisions
│   │   ├── pricing_engine.py         # Premium calculation
│   │   ├── risk_assessment.py        # Risk scoring
│   │   ├── underwriting.py           # Underwriting logic
│   │   ├── claims_processor.py       # Claims handling
│   │   ├── fraud_detection.py        # Fraud checks
│   │   ├── document_processor.py     # Document handling
│   │   ├── notification.py           # Notifications
│   │   ├── reporting.py              # Report generation
│   │   ├── external/                 # External services
│   │   │   ├── __init__.py
│   │   │   ├── credit_check.py      # Credit bureaus
│   │   │   ├── kyc_verification.py   # KYC services
│   │   │   ├── payment_gateway.py    # Payment processing
│   │   │   ├── email_service.py      # Email provider
│   │   │   ├── sms_service.py        # SMS provider
│   │   │   └── storage_service.py    # Cloud storage
│   │   └── ml/                       # ML services
│   │       ├── __init__.py
│   │       ├── risk_predictor.py     # Risk prediction
│   │       ├── fraud_detector.py     # Fraud ML models
│   │       └── pricing_optimizer.py   # Price optimization
│   │
│   ├── db/                           # Database layer
│   │   ├── __init__.py
│   │   ├── base.py                   # Database base
│   │   ├── session.py                # Session management
│   │   ├── repositories/             # Data repositories
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Base repository
│   │   │   ├── policy.py            # Policy repository
│   │   │   ├── quote.py             # Quote repository
│   │   │   ├── claim.py             # Claim repository
│   │   │   ├── customer.py          # Customer repository
│   │   │   └── audit.py             # Audit repository
│   │   └── queries/                  # Complex queries
│   │       ├── __init__.py
│   │       ├── analytics.py          # Analytics queries
│   │       └── reports.py            # Report queries
│   │
│   ├── tasks/                        # Background tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py             # Celery configuration
│   │   ├── policy_tasks.py           # Policy-related tasks
│   │   ├── notification_tasks.py     # Notification tasks
│   │   ├── report_tasks.py           # Report generation
│   │   ├── cleanup_tasks.py          # Data cleanup
│   │   └── scheduled_tasks.py        # Scheduled jobs
│   │
│   └── utils/                        # Utilities
│       ├── __init__.py
│       ├── validators.py             # Custom validators
│       ├── formatters.py             # Data formatters
│       ├── calculators.py            # Business calculators
│       ├── decorators.py             # Custom decorators
│       ├── cache.py                  # Caching utilities
│       ├── date_utils.py             # Date handling
│       ├── money.py                  # Currency handling
│       └── insurance_helpers.py      # Insurance utilities
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration
│   ├── factories.py                  # Test data factories
│   ├── fixtures/                     # Test fixtures
│   │   ├── __init__.py
│   │   ├── policies.py
│   │   ├── quotes.py
│   │   └── customers.py
│   ├── unit/                         # Unit tests
│   │   ├── __init__.py
│   │   ├── test_models/
│   │   ├── test_services/
│   │   ├── test_utils/
│   │   └── test_schemas/
│   ├── integration/                  # Integration tests
│   │   ├── __init__.py
│   │   ├── test_api/
│   │   ├── test_db/
│   │   └── test_external/
│   ├── e2e/                          # End-to-end tests
│   │   ├── __init__.py
│   │   ├── test_policy_flow.py
│   │   ├── test_claim_flow.py
│   │   └── test_quote_flow.py
│   └── performance/                  # Performance tests
│       ├── __init__.py
│       ├── test_load.py
│       └── test_stress.py
│
├── alembic/                          # Database migrations
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── scripts/                          # Utility scripts
│   ├── __init__.py
│   ├── seed_data.py                  # Database seeding
│   ├── migrate_data.py               # Data migration
│   ├── generate_reports.py           # Report generation
│   ├── backup_db.py                  # Database backup
│   └── health_check.py               # Health monitoring
│
├── docker/                           # Docker files
│   ├── Dockerfile                    # Main Dockerfile
│   ├── Dockerfile.dev                # Development Dockerfile
│   ├── docker-compose.yml            # Docker Compose
│   ├── docker-compose.override.yml   # Dev overrides
│   └── scripts/                      # Docker scripts
│       ├── entrypoint.sh
│       └── wait-for-it.sh
│
├── docs/                             # Documentation
│   ├── api/                          # API documentation
│   ├── architecture/                 # Architecture docs
│   ├── deployment/                   # Deployment guides
│   └── development/                  # Dev guides
│
├── .github/                          # GitHub configuration
│   ├── workflows/                    # GitHub Actions
│   │   ├── test.yml
│   │   ├── lint.yml
│   │   └── deploy.yml
│   └── PULL_REQUEST_TEMPLATE.md
│
├── config/                           # Configuration files
│   ├── logging.yaml                  # Logging config
│   ├── gunicorn.conf.py             # Gunicorn config
│   └── nginx.conf                    # Nginx config
│
├── requirements/                     # Requirements files
│   ├── base.txt                      # Base requirements
│   ├── dev.txt                       # Development deps
│   ├── test.txt                      # Testing deps
│   └── prod.txt                      # Production deps
│
├── .env.example                      # Environment example
├── .gitignore                        # Git ignore file
├── .dockerignore                     # Docker ignore file
├── .pre-commit-config.yaml           # Pre-commit hooks
├── Makefile                          # Make commands
├── pyproject.toml                    # Project config
├── setup.py                          # Package setup
├── README.md                         # Project README
├── CHANGELOG.md                      # Change log
└── LICENSE                           # License file
```

## Key Design Principles

### 1. Domain-Driven Design
- Models represent insurance domain concepts
- Services implement business logic
- Clear separation between API and domain layers

### 2. Dependency Injection
- Use FastAPI's dependency system
- Inject services into endpoints
- Easy testing with mock dependencies

### 3. Repository Pattern
- Abstract database operations
- Separate business logic from data access
- Support multiple data sources

### 4. Clean Architecture
- Dependencies point inward
- Domain models don't depend on frameworks
- External services behind interfaces

### 5. Async-First Design
- All endpoints are async
- Use asyncio for concurrent operations
- Async database queries with SQLAlchemy

## Module Descriptions

### `/app/api/`
API layer handling HTTP requests, authentication, and response formatting.

### `/app/core/`
Core utilities, configuration, and cross-cutting concerns.

### `/app/models/`
Domain models representing insurance entities (SQLAlchemy models).

### `/app/schemas/`
Pydantic models for request/response validation and serialization.

### `/app/services/`
Business logic implementation, including external service integrations.

### `/app/db/`
Database access layer with repositories and complex queries.

### `/app/tasks/`
Background job processing using Celery for async operations.

### `/app/utils/`
Utility functions and helpers specific to insurance domain.

## Configuration Management

### Environment Variables
```python
# app/config.py
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # Application
    app_name: str = Field("Insurance API", env="APP_NAME")
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    
    # API
    api_prefix: str = Field("/api/v1", env="API_PREFIX")
    cors_origins: list[str] = Field([], env="CORS_ORIGINS")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    db_pool_size: int = Field(5, env="DB_POOL_SIZE")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # External Services
    underwriting_api_url: str = Field(..., env="UNDERWRITING_API_URL")
    underwriting_api_key: str = Field(..., env="UNDERWRITING_API_KEY")
    
    # Redis
    redis_url: str = Field(..., env="REDIS_URL")
    
    # Insurance-specific
    max_policy_amount: float = Field(10000000, env="MAX_POLICY_AMOUNT")
    min_driver_age: int = Field(18, env="MIN_DRIVER_AGE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Focus on business logic

### Integration Tests
- Test component interactions
- Use test database
- Verify API contracts

### End-to-End Tests
- Test complete user flows
- Simulate real user scenarios
- Verify system behavior

### Performance Tests
- Load testing with Locust
- Stress testing critical endpoints
- Monitor resource usage

## Development Workflow

### 1. Local Development
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements/dev.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### 2. Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test category
pytest -m unit
pytest -m integration
```

### 3. Code Quality
```bash
# Type checking
mypy app/

# Linting
flake8 app/
black app/
isort app/

# Security scan
bandit -r app/
```

### 4. Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## Deployment Considerations

### 1. Production Configuration
- Use environment-specific settings
- Enable security headers
- Configure proper logging
- Set up monitoring

### 2. Database Migrations
- Run migrations before deployment
- Test rollback procedures
- Backup database before major changes

### 3. Scaling
- Use connection pooling
- Implement caching strategy
- Consider read replicas
- Use background jobs for heavy tasks

### 4. Monitoring
- Application metrics with Prometheus
- Distributed tracing with Jaeger
- Centralized logging with ELK
- Error tracking with Sentry