# FastAPI Insurance API Starter

A production-ready FastAPI template for building insurance policy decision APIs with async patterns, type safety, and comprehensive testing.

## Features

- **Async API Endpoints**: High-performance async handlers for policy decisions
- **Type Safety**: Full type annotations with Pydantic models
- **Structured Logging**: JSON logging with correlation IDs
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Testing**: Pytest setup with async test support
- **Documentation**: Auto-generated OpenAPI/Swagger docs
- **Health Checks**: Ready and liveness endpoints
- **Metrics**: Prometheus metrics integration
- **Security**: API key authentication and rate limiting

## Project Structure

```
insurance-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration management
│   ├── dependencies.py      # Dependency injection
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── policies.py      # Policy decision endpoints
│   │   │   │   ├── quotes.py        # Quote generation endpoints
│   │   │   │   ├── claims.py        # Claims processing endpoints
│   │   │   │   └── health.py        # Health check endpoints
│   │   │   └── dependencies.py      # API-specific dependencies
│   │   └── middleware.py             # Custom middleware
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                 # Core configuration
│   │   ├── security.py               # Security utilities
│   │   ├── exceptions.py             # Custom exceptions
│   │   └── logging.py                # Logging configuration
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── policy.py                 # Policy domain models
│   │   ├── quote.py                  # Quote models
│   │   ├── claim.py                  # Claim models
│   │   └── common.py                 # Shared models
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── policy.py                 # Policy API schemas
│   │   ├── quote.py                  # Quote API schemas
│   │   ├── claim.py                  # Claim API schemas
│   │   └── responses.py              # Response schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── policy_engine.py          # Policy decision logic
│   │   ├── pricing_engine.py         # Pricing calculations
│   │   ├── risk_assessment.py        # Risk scoring
│   │   └── external/                 # External service clients
│   │       ├── __init__.py
│   │       ├── underwriting.py
│   │       └── fraud_detection.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py             # Custom validators
│       ├── formatters.py             # Data formatters
│       └── constants.py              # Application constants
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── alembic/                          # Database migrations
├── scripts/                          # Utility scripts
├── docker/                           # Docker configurations
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd insurance-api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run Development Server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Run Tests**
   ```bash
   pytest
   pytest --cov=app tests/
   ```

## API Examples

### Policy Decision Endpoint

```python
# app/api/v1/endpoints/policies.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.policy import PolicyDecisionRequest, PolicyDecisionResponse
from app.services.policy_engine import PolicyEngine
from app.core.dependencies import get_policy_engine

router = APIRouter()

@router.post("/decisions", response_model=PolicyDecisionResponse)
async def create_policy_decision(
    request: PolicyDecisionRequest,
    policy_engine: PolicyEngine = Depends(get_policy_engine)
) -> PolicyDecisionResponse:
    """
    Evaluate policy eligibility and generate decision.
    """
    try:
        decision = await policy_engine.evaluate_policy(request)
        return PolicyDecisionResponse(
            decision_id=decision.id,
            status=decision.status,
            premium=decision.premium,
            coverage_details=decision.coverage_details,
            conditions=decision.conditions
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Quote Generation with Async External Calls

```python
# app/api/v1/endpoints/quotes.py
import asyncio
from fastapi import APIRouter, Depends
from app.schemas.quote import QuoteRequest, QuoteResponse
from app.services.pricing_engine import PricingEngine
from app.services.external.underwriting import UnderwritingClient

router = APIRouter()

@router.post("/generate", response_model=QuoteResponse)
async def generate_quote(
    request: QuoteRequest,
    pricing_engine: PricingEngine = Depends(get_pricing_engine),
    underwriting_client: UnderwritingClient = Depends(get_underwriting_client)
) -> QuoteResponse:
    """
    Generate insurance quote with risk assessment.
    """
    # Parallel async calls for better performance
    risk_assessment, underwriting_result = await asyncio.gather(
        pricing_engine.assess_risk(request),
        underwriting_client.check_eligibility(request)
    )
    
    quote = await pricing_engine.calculate_quote(
        request=request,
        risk_score=risk_assessment.score,
        underwriting_flags=underwriting_result.flags
    )
    
    return QuoteResponse(
        quote_id=quote.id,
        premium=quote.premium,
        deductible=quote.deductible,
        coverage_limits=quote.coverage_limits,
        valid_until=quote.expiry_date
    )
```

## Configuration

### Environment Variables

```bash
# Application
APP_NAME=insurance-api
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# API
API_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000"]

# Security
API_KEY_HEADER=X-API-Key
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/insurance_db

# External Services
UNDERWRITING_SERVICE_URL=https://underwriting.example.com
FRAUD_SERVICE_URL=https://fraud-detection.example.com
FRAUD_SERVICE_API_KEY=your-api-key

# Redis (for caching/rate limiting)
REDIS_URL=redis://localhost:6379

# Monitoring
ENABLE_METRICS=true
METRICS_PATH=/metrics
```

## Testing

### Unit Test Example

```python
# tests/unit/test_policy_engine.py
import pytest
from app.services.policy_engine import PolicyEngine
from app.schemas.policy import PolicyDecisionRequest

@pytest.mark.asyncio
async def test_policy_decision_auto_approve():
    engine = PolicyEngine()
    request = PolicyDecisionRequest(
        applicant_age=35,
        coverage_amount=500000,
        policy_type="term_life",
        health_conditions=[]
    )
    
    decision = await engine.evaluate_policy(request)
    
    assert decision.status == "approved"
    assert decision.premium > 0
    assert len(decision.conditions) == 0
```

### Integration Test Example

```python
# tests/integration/test_quote_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_generate_quote_success():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/quotes/generate",
            json={
                "policy_type": "auto",
                "vehicle_year": 2022,
                "vehicle_make": "Toyota",
                "vehicle_model": "Camry",
                "driver_age": 30,
                "driving_history": "clean"
            },
            headers={"X-API-Key": "test-key"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "quote_id" in data
    assert data["premium"] > 0
```

## Production Considerations

1. **Performance**
   - Use connection pooling for database
   - Implement Redis caching for frequent queries
   - Add request/response compression
   - Use async wherever possible

2. **Security**
   - Enable HTTPS only
   - Implement rate limiting
   - Add request validation
   - Use API key rotation
   - Implement audit logging

3. **Monitoring**
   - Add structured logging
   - Export Prometheus metrics
   - Implement distributed tracing
   - Set up alerting rules

4. **Deployment**
   - Use multi-stage Docker builds
   - Implement health checks
   - Add graceful shutdown
   - Use environment-specific configs