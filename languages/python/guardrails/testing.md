---
name: Testing
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# Python Testing Requirements

## Overview

This document defines comprehensive testing requirements for Python applications, with specific focus on insurance domain scenarios. All Python projects must adhere to these testing standards to ensure reliability, maintainability, and quality.

## Coverage Requirements

### Minimum Coverage Targets
- **Overall Code Coverage**: Minimum 80%
- **Critical Business Logic**: Minimum 95%
- **API Endpoints**: 100%
- **Data Models**: 90%
- **Utility Functions**: 85%

### Coverage Configuration
```ini
# .coveragerc
[run]
source = src/
omit = 
    */tests/*
    */migrations/*
    */__init__.py
    */config/*
    */venv/*

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov

[xml]
output = coverage.xml
```

## Unit Testing Patterns

### Async Code Testing
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

# Test async functions with pytest-asyncio
@pytest.mark.asyncio
async def test_calculate_premium_async():
    """Test asynchronous premium calculation."""
    from src.services.premium_calculator import calculate_premium_async
    
    # Mock external API calls
    with patch('src.services.external_api.get_risk_score') as mock_risk:
        mock_risk.return_value = AsyncMock(return_value=0.75)
        
        result = await calculate_premium_async(
            coverage_amount=100000,
            policy_type="term_life",
            customer_age=35
        )
        
        assert result.premium_amount > 0
        assert result.calculation_time < 1.0  # Performance assertion
        mock_risk.assert_called_once()

# Test async context managers
@pytest.mark.asyncio
async def test_database_transaction():
    """Test async database transaction handling."""
    from src.db.session import AsyncDatabaseSession
    
    async with AsyncDatabaseSession() as session:
        # Test transaction rollback on error
        with pytest.raises(ValueError):
            async with session.begin():
                await session.execute("INSERT INTO policies ...")
                raise ValueError("Simulated error")
        
        # Verify rollback occurred
        result = await session.execute("SELECT COUNT(*) FROM policies")
        assert result.scalar() == 0

# Test concurrent async operations
@pytest.mark.asyncio
async def test_concurrent_quote_generation():
    """Test concurrent quote generation for multiple customers."""
    from src.services.quote_service import generate_quote_async
    
    customer_ids = [1, 2, 3, 4, 5]
    
    # Generate quotes concurrently
    quotes = await asyncio.gather(*[
        generate_quote_async(customer_id) 
        for customer_id in customer_ids
    ])
    
    assert len(quotes) == 5
    assert all(quote.status == "generated" for quote in quotes)
```

### Mocking Patterns
```python
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

def test_policy_renewal_with_mocks():
    """Test policy renewal with mocked dependencies."""
    # Mock the payment service
    mock_payment_service = Mock()
    mock_payment_service.process_payment.return_value = {
        "status": "success",
        "transaction_id": "TXN123456"
    }
    
    # Mock the notification service
    mock_notification_service = Mock()
    
    # Test the renewal process
    from src.services.policy_service import PolicyService
    
    service = PolicyService(
        payment_service=mock_payment_service,
        notification_service=mock_notification_service
    )
    
    result = service.renew_policy(
        policy_id="POL123",
        payment_method="credit_card"
    )
    
    # Verify interactions
    mock_payment_service.process_payment.assert_called_once()
    mock_notification_service.send_renewal_confirmation.assert_called_once()
    
    assert result.status == "renewed"
    assert result.next_renewal_date > datetime.now()
```

## Integration Testing

### TestContainers Setup
```python
# conftest.py
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.kafka import KafkaContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def postgres_container():
    """Provide a PostgreSQL container for integration tests."""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def redis_container():
    """Provide a Redis container for caching tests."""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis

@pytest.fixture(scope="session")
def kafka_container():
    """Provide a Kafka container for event streaming tests."""
    with KafkaContainer("confluentinc/cp-kafka:7.5.0") as kafka:
        yield kafka

@pytest.fixture
def db_session(postgres_container):
    """Provide a database session for tests."""
    engine = create_engine(postgres_container.get_connection_url())
    SessionLocal = sessionmaker(bind=engine)
    
    # Create tables
    from src.models import Base
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)

# Integration test example
def test_claim_processing_integration(db_session, redis_container, kafka_container):
    """Test full claim processing workflow with real dependencies."""
    from src.services.claim_processor import ClaimProcessor
    from src.models import Claim, Policy
    
    # Setup test data
    policy = Policy(
        policy_number="POL123",
        coverage_amount=100000,
        status="active"
    )
    db_session.add(policy)
    db_session.commit()
    
    # Configure processor with real connections
    processor = ClaimProcessor(
        db_session=db_session,
        redis_url=redis_container.get_connection_url(),
        kafka_bootstrap_servers=kafka_container.get_bootstrap_server()
    )
    
    # Submit and process claim
    claim_data = {
        "policy_id": policy.id,
        "claim_amount": 5000,
        "incident_date": "2024-01-15",
        "description": "Medical expenses"
    }
    
    result = processor.process_claim(claim_data)
    
    # Verify database state
    claim = db_session.query(Claim).filter_by(id=result.claim_id).first()
    assert claim is not None
    assert claim.status == "submitted"
    
    # Verify event was published
    # Consumer would verify Kafka message here
```

## Property-Based Testing

### Hypothesis Configuration
```python
# test_calculations.py
import hypothesis
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import decimals, integers, dates
from decimal import Decimal
import datetime

# Configure Hypothesis
hypothesis.settings.register_profile(
    "ci",
    max_examples=1000,
    deadline=5000,  # 5 seconds
    database=None,  # Don't save examples in CI
)

hypothesis.settings.register_profile(
    "dev",
    max_examples=100,
    deadline=2000,
)

# Property-based tests for insurance calculations
class TestPremiumCalculations:
    @given(
        age=integers(min_value=18, max_value=85),
        coverage=decimals(
            min_value=Decimal("10000"), 
            max_value=Decimal("5000000"),
            places=2
        ),
        health_score=decimals(
            min_value=Decimal("0.1"),
            max_value=Decimal("1.0"),
            places=2
        )
    )
    def test_premium_calculation_properties(self, age, coverage, health_score):
        """Test premium calculation maintains expected properties."""
        from src.calculations.premium import calculate_life_premium
        
        premium = calculate_life_premium(
            age=age,
            coverage_amount=coverage,
            health_score=health_score
        )
        
        # Property 1: Premium should always be positive
        assert premium > 0
        
        # Property 2: Premium should be less than coverage amount
        assert premium < coverage
        
        # Property 3: Premium should scale with age (older = higher)
        if age > 50:
            young_premium = calculate_life_premium(25, coverage, health_score)
            assert premium > young_premium
        
        # Property 4: Premium should inversely scale with health score
        if health_score < Decimal("0.5"):
            healthy_premium = calculate_life_premium(age, coverage, Decimal("0.9"))
            assert premium > healthy_premium

    @given(
        claim_amount=decimals(
            min_value=Decimal("100"),
            max_value=Decimal("100000"),
            places=2
        ),
        deductible=decimals(
            min_value=Decimal("0"),
            max_value=Decimal("5000"),
            places=2
        ),
        coverage_limit=decimals(
            min_value=Decimal("10000"),
            max_value=Decimal("1000000"),
            places=2
        )
    )
    @settings(max_examples=200)
    def test_claim_payout_calculation(self, claim_amount, deductible, coverage_limit):
        """Test claim payout calculation properties."""
        from src.calculations.claims import calculate_payout
        
        payout = calculate_payout(
            claim_amount=claim_amount,
            deductible=deductible,
            coverage_limit=coverage_limit
        )
        
        # Property 1: Payout should never exceed claim amount minus deductible
        assert payout <= max(claim_amount - deductible, 0)
        
        # Property 2: Payout should never exceed coverage limit
        assert payout <= coverage_limit
        
        # Property 3: Payout should be zero if claim is less than deductible
        if claim_amount <= deductible:
            assert payout == 0
        
        # Property 4: Payout should be non-negative
        assert payout >= 0

# Test with date ranges
@given(
    policy_start=dates(
        min_value=datetime.date(2020, 1, 1),
        max_value=datetime.date(2024, 12, 31)
    ),
    claim_date=dates(
        min_value=datetime.date(2020, 1, 1),
        max_value=datetime.date(2025, 12, 31)
    )
)
def test_policy_validity_check(policy_start, claim_date):
    """Test policy validity checking logic."""
    from src.validators.policy import is_claim_within_policy_period
    
    policy_end = policy_start + datetime.timedelta(days=365)
    
    is_valid = is_claim_within_policy_period(
        policy_start=policy_start,
        policy_end=policy_end,
        claim_date=claim_date
    )
    
    # Property: Claim is valid only if within policy period
    expected = policy_start <= claim_date <= policy_end
    assert is_valid == expected
```

## Performance Testing

### Locust Configuration
```python
# locustfile.py
from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
import json
import random
import gevent

class InsuranceAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get authentication token."""
        response = self.client.post("/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def get_quote(self):
        """Test quote generation endpoint."""
        quote_data = {
            "coverage_type": random.choice(["life", "health", "auto"]),
            "coverage_amount": random.randint(50000, 500000),
            "customer_age": random.randint(25, 65),
            "zip_code": random.choice(["10001", "90210", "60601"])
        }
        
        with self.client.post(
            "/api/quotes/generate",
            json=quote_data,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.elapsed.total_seconds() > 2.0:
                response.failure("Quote generation took too long")
            elif response.status_code == 200:
                response.success()
    
    @task(2)
    def search_policies(self):
        """Test policy search endpoint."""
        params = {
            "status": random.choice(["active", "expired", "pending"]),
            "limit": 20,
            "offset": random.randint(0, 100)
        }
        
        self.client.get(
            "/api/policies",
            params=params,
            headers=self.headers,
            name="/api/policies?status=[status]"
        )
    
    @task(1)
    def submit_claim(self):
        """Test claim submission endpoint."""
        claim_data = {
            "policy_id": random.randint(1000, 9999),
            "claim_type": random.choice(["medical", "accident", "theft"]),
            "amount": random.randint(100, 10000),
            "description": "Test claim submission",
            "incident_date": "2024-01-15"
        }
        
        self.client.post(
            "/api/claims",
            json=claim_data,
            headers=self.headers
        )

# Custom performance thresholds
@events.request.add_listener
def check_response_time(request_type, name, response_time, **kwargs):
    """Check if response times meet SLA requirements."""
    thresholds = {
        "/api/quotes/generate": 2000,  # 2 seconds
        "/api/policies": 500,           # 500ms
        "/api/claims": 1000            # 1 second
    }
    
    if name in thresholds and response_time > thresholds[name]:
        print(f"WARNING: {name} exceeded threshold: {response_time}ms > {thresholds[name]}ms")

# Load test scenarios
class QuoteSpikeTest(HttpUser):
    """Simulate spike in quote requests during marketing campaign."""
    wait_time = between(0.1, 0.5)
    
    @task
    def rapid_quotes(self):
        """Generate quotes rapidly."""
        for _ in range(10):
            self.client.post("/api/quotes/generate", json={
                "coverage_type": "auto",
                "coverage_amount": 50000,
                "customer_age": 30
            })

# Performance test configuration
# Run with: locust -f locustfile.py --host=http://localhost:8000
# For CI/CD: locust -f locustfile.py --headless -u 100 -r 10 -t 5m --html report.html
```

## Contract Testing

### Pact Testing Setup
```python
# test_contracts.py
import pytest
from pact import Consumer, Provider, Like, EachLike, Format
import json
from datetime import datetime

# Consumer contract tests
@pytest.fixture
def pact():
    """Setup Pact consumer."""
    consumer = Consumer('InsuranceWebApp')
    provider = Provider('InsuranceAPI')
    
    pact = consumer.has_pact_with(
        provider,
        host_name='localhost',
        port=1234,
        pact_dir='./pacts'
    )
    
    pact.start_service()
    yield pact
    pact.stop_service()

def test_get_policy_contract(pact):
    """Test contract for getting policy details."""
    expected = {
        "id": Like(123),
        "policy_number": Like("POL-123456"),
        "holder_name": Like("John Doe"),
        "coverage_amount": Like(100000.00),
        "premium": Like(150.00),
        "start_date": Format().iso_8601_datetime(),
        "end_date": Format().iso_8601_datetime(),
        "status": Like("active"),
        "coverage_details": EachLike({
            "type": Like("medical"),
            "limit": Like(50000.00),
            "deductible": Like(500.00)
        })
    }
    
    (pact
     .given('a policy exists')
     .upon_receiving('a request for policy details')
     .with_request('GET', '/api/policies/123')
     .will_respond_with(200, body=expected))
    
    with pact:
        # Make actual request
        import requests
        response = requests.get(pact.uri + '/api/policies/123')
        
        assert response.status_code == 200
        data = response.json()
        assert data['policy_number'].startswith('POL-')
        assert data['status'] in ['active', 'expired', 'suspended']

def test_create_claim_contract(pact):
    """Test contract for creating a new claim."""
    request_body = {
        "policy_id": 123,
        "claim_type": "medical",
        "amount": 1500.00,
        "incident_date": "2024-01-15",
        "description": "Emergency room visit"
    }
    
    expected_response = {
        "claim_id": Like("CLM-789012"),
        "status": Like("submitted"),
        "submitted_at": Format().iso_8601_datetime(),
        "estimated_processing_time": Like(5),
        "next_steps": EachLike("Document upload required")
    }
    
    (pact
     .given('a valid policy exists')
     .upon_receiving('a claim submission')
     .with_request('POST', '/api/claims', body=request_body)
     .will_respond_with(201, body=expected_response))
    
    with pact:
        import requests
        response = requests.post(
            pact.uri + '/api/claims',
            json=request_body
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['claim_id'].startswith('CLM-')
        assert data['status'] == 'submitted'

# Provider verification
def test_provider_honors_consumer_contract():
    """Verify provider meets consumer expectations."""
    from pact import Verifier
    
    verifier = Verifier(
        provider='InsuranceAPI',
        provider_base_url='http://localhost:8000'
    )
    
    # Configure provider states
    verifier.set_state_handler_setup(setup_provider_state)
    verifier.set_state_handler_teardown(teardown_provider_state)
    
    # Verify all pacts
    output, logs = verifier.verify_pacts(
        './pacts/insurancewebapp-insuranceapi.json',
        verbose=True,
        provider_states_setup_url='http://localhost:8000/pact/setup',
        enable_pending=True
    )
    
    assert output == 0

def setup_provider_state(state):
    """Setup provider state for contract testing."""
    if state == 'a policy exists':
        # Create test policy in database
        create_test_policy(id=123, policy_number="POL-123456")
    elif state == 'a valid policy exists':
        # Create active policy for claim submission
        create_test_policy(id=123, status="active")

def teardown_provider_state(state):
    """Cleanup provider state after contract testing."""
    # Clean up test data
    cleanup_test_data()
```

## Test Data Management

### Insurance-Specific Test Data
```python
# test_data_factory.py
import factory
from factory import fuzzy
from faker import Faker
from datetime import datetime, timedelta
import random
from decimal import Decimal

fake = Faker()

class PolicyFactory(factory.Factory):
    """Factory for creating test insurance policies."""
    class Meta:
        model = dict
    
    policy_number = factory.LazyFunction(
        lambda: f"POL-{fake.random_int(100000, 999999)}"
    )
    holder_name = factory.Faker('name')
    holder_email = factory.Faker('email')
    holder_phone = factory.Faker('phone_number')
    
    coverage_type = factory.fuzzy.FuzzyChoice([
        'life', 'health', 'auto', 'home', 'disability'
    ])
    coverage_amount = factory.LazyFunction(
        lambda: Decimal(random.choice([
            50000, 100000, 250000, 500000, 1000000
        ]))
    )
    
    start_date = factory.Faker(
        'date_between',
        start_date='-2y',
        end_date='today'
    )
    end_date = factory.LazyAttribute(
        lambda obj: obj.start_date + timedelta(days=365)
    )
    
    premium = factory.LazyAttribute(
        lambda obj: Decimal(obj.coverage_amount * Decimal('0.002'))
    )
    
    status = factory.fuzzy.FuzzyChoice(
        ['active', 'expired', 'suspended', 'cancelled'],
        weights=[70, 15, 10, 5]
    )

class ClaimFactory(factory.Factory):
    """Factory for creating test insurance claims."""
    class Meta:
        model = dict
    
    claim_number = factory.LazyFunction(
        lambda: f"CLM-{fake.random_int(100000, 999999)}"
    )
    policy_id = factory.Faker('random_int', min=1, max=1000)
    
    claim_type = factory.fuzzy.FuzzyChoice([
        'medical', 'accident', 'theft', 'damage', 'liability'
    ])
    
    amount_claimed = factory.fuzzy.FuzzyDecimal(
        100, 50000, precision=2
    )
    amount_approved = factory.LazyAttribute(
        lambda obj: Decimal(obj.amount_claimed * Decimal('0.8'))
    )
    
    incident_date = factory.Faker(
        'date_between',
        start_date='-6m',
        end_date='today'
    )
    filed_date = factory.LazyAttribute(
        lambda obj: obj.incident_date + timedelta(days=random.randint(1, 30))
    )
    
    status = factory.fuzzy.FuzzyChoice([
        'submitted', 'under_review', 'approved', 'rejected', 'paid'
    ])
    
    description = factory.Faker('paragraph', nb_sentences=3)

class CustomerFactory(factory.Factory):
    """Factory for creating test customer profiles."""
    class Meta:
        model = dict
    
    customer_id = factory.Faker('uuid4')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    date_of_birth = factory.Faker(
        'date_of_birth',
        minimum_age=18,
        maximum_age=85
    )
    
    # Risk factors for insurance
    smoker = factory.Faker('boolean', chance_of_getting_true=20)
    pre_existing_conditions = factory.LazyFunction(
        lambda: random.sample([
            'diabetes', 'hypertension', 'asthma', 'none'
        ], k=random.randint(0, 2))
    )
    
    driving_record = factory.fuzzy.FuzzyChoice([
        'clean', 'minor_violations', 'major_violations'
    ], weights=[70, 25, 5])
    
    credit_score = factory.fuzzy.FuzzyInteger(300, 850)
    
    # Address information
    address = factory.Faker('street_address')
    city = factory.Faker('city')
    state = factory.Faker('state_abbr')
    zip_code = factory.Faker('zipcode')

# Test data scenarios
class TestDataScenarios:
    """Generate specific test data scenarios for insurance testing."""
    
    @staticmethod
    def high_risk_customer():
        """Generate a high-risk customer profile."""
        return CustomerFactory(
            age=75,
            smoker=True,
            pre_existing_conditions=['diabetes', 'hypertension'],
            driving_record='major_violations',
            credit_score=random.randint(300, 500)
        )
    
    @staticmethod
    def low_risk_customer():
        """Generate a low-risk customer profile."""
        return CustomerFactory(
            age=30,
            smoker=False,
            pre_existing_conditions=[],
            driving_record='clean',
            credit_score=random.randint(750, 850)
        )
    
    @staticmethod
    def expired_policy():
        """Generate an expired policy."""
        return PolicyFactory(
            status='expired',
            end_date=fake.date_between(
                start_date='-1y',
                end_date='-1d'
            )
        )
    
    @staticmethod
    def complex_claim():
        """Generate a complex claim scenario."""
        return {
            'primary_claim': ClaimFactory(
                claim_type='accident',
                amount_claimed=50000
            ),
            'medical_claims': [
                ClaimFactory(claim_type='medical')
                for _ in range(3)
            ],
            'property_claim': ClaimFactory(
                claim_type='damage',
                amount_claimed=25000
            )
        }

# Fixture for test data
@pytest.fixture
def test_data_generator():
    """Provide test data generator for tests."""
    return {
        'policy': PolicyFactory,
        'claim': ClaimFactory,
        'customer': CustomerFactory,
        'scenarios': TestDataScenarios
    }
```

## CI/CD Integration

### GitHub Actions Configuration
```yaml
# .github/workflows/python-tests.yml
name: Python Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run linting
      run: |
        flake8 src tests
        black --check src tests
        isort --check-only src tests
        mypy src
    
    - name: Run security checks
      run: |
        bandit -r src
        safety check
    
    - name: Run unit tests with coverage
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/unit \
          --cov=src \
          --cov-report=xml \
          --cov-report=html \
          --cov-report=term-missing \
          --cov-fail-under=80
    
    - name: Run integration tests
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/integration \
          --maxfail=5 \
          --tb=short
    
    - name: Run property-based tests
      run: |
        pytest tests/property \
          --hypothesis-profile=ci
    
    - name: Run contract tests
      run: |
        pytest tests/contracts
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-${{ matrix.python-version }}
    
    - name: Run performance tests
      if: github.event_name == 'pull_request'
      run: |
        locust -f tests/performance/locustfile.py \
          --headless \
          --users 50 \
          --spawn-rate 5 \
          --run-time 2m \
          --host http://localhost:8000 \
          --html performance-report.html \
          --only-summary
    
    - name: Upload test artifacts
      if: failure()
      uses: actions/upload-artifact@v3
      with:
        name: test-results-${{ matrix.python-version }}
        path: |
          htmlcov/
          performance-report.html
          .coverage
          pytest-report.xml

  test-mutations:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install mutmut
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run mutation testing
      run: |
        mutmut run \
          --paths-to-mutate=src/ \
          --tests-dir=tests/unit/ \
          --runner="pytest -x" \
          --use-coverage
    
    - name: Show mutation results
      if: always()
      run: |
        mutmut results
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
  
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203"]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
  
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/unit --tb=short --quiet --maxfail=1
        language: system
        pass_filenames: false
        always_run: true
```

## Best Practices

### Test Organization
1. **Directory Structure**:
   ```
   tests/
   ├── unit/
   │   ├── test_models.py
   │   ├── test_services.py
   │   └── test_calculations.py
   ├── integration/
   │   ├── test_api_endpoints.py
   │   └── test_database_operations.py
   ├── property/
   │   ├── test_premium_calculations.py
   │   └── test_claim_processing.py
   ├── performance/
   │   └── locustfile.py
   ├── contracts/
   │   └── test_api_contracts.py
   └── conftest.py
   ```

2. **Naming Conventions**:
   - Test files: `test_*.py`
   - Test classes: `Test*`
   - Test methods: `test_*`
   - Use descriptive names that explain what is being tested

3. **Test Independence**:
   - Each test should be independent and not rely on other tests
   - Use fixtures for shared setup
   - Clean up test data after each test

4. **Assertion Best Practices**:
   - Use specific assertions rather than generic `assert`
   - Include meaningful error messages
   - Test one concept per test method

5. **Mock Usage Guidelines**:
   - Mock external dependencies, not internal components
   - Verify mock interactions when testing integrations
   - Use real implementations in integration tests

### Performance Considerations
1. **Test Execution Speed**:
   - Use pytest-xdist for parallel test execution
   - Minimize database operations in unit tests
   - Use in-memory databases for faster tests

2. **Resource Management**:
   - Properly cleanup resources in teardown
   - Use context managers for resource management
   - Monitor test memory usage

3. **Continuous Monitoring**:
   - Track test execution times
   - Monitor coverage trends
   - Set up alerts for failing tests in CI/CD