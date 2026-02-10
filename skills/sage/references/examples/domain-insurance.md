# Domain Example: Property & Casualty Insurance

This reference shows how a specific business domain maps to the SAGE framework.
Use it as a template when creating new domain modules. Load this reference only
when users need a concrete domain example or are building insurance systems.

## Domain Overview

P&C (Property & Casualty) insurance automates policy decisions including underwriting,
rating, claims assessment, and renewal evaluations. The domain requires strict
compliance with state-specific regulations, actuarial accuracy, and audit trails.

## System Architecture (Insurance-Specific)

```
External Systems Layer
  ├── CRM Systems (Salesforce, HubSpot)
  ├── Rating APIs (ISO, AAIS)
  ├── Regulatory Databases (NAIC, state DOIs)
  └── Document Management (policy forms, endorsements)

Integration Layer
  ├── API Gateway (auth, rate limiting, routing)
  ├── Message Queue (async claim processing)
  └── Event Streaming (policy lifecycle events)

Decision Engine Layer
  ├── Rule Engine (underwriting rules, compliance checks)
  ├── Risk Scorer (ML-powered risk assessment)
  └── Decision Logger (immutable audit trail)

Domain Services Layer
  ├── Underwriting Service
  ├── Rating Engine Service
  ├── Claims Processing Service
  ├── Policy Administration Service
  ├── Compliance Engine Service
  └── Customer Service

Data Layer
  ├── Policy Store (PostgreSQL — ACID transactions)
  ├── Event Store (Kafka — event sourcing)
  ├── Cache Layer (Redis — rate tables, territory data)
  └── Search Index (Elasticsearch — policy search)
```

## Core Business Entities

### Policy
- Represents an insurance contract between insurer and insured
- Has lifecycle: Quote → Bind → Active → Renewal → Cancellation
- Contains coverages, premium breakdowns, and endorsements
- Must comply with state-specific form requirements

### Claim
- Filed against a policy when a covered loss occurs
- Lifecycle: FNOL → Investigation → Reserve → Payment → Close
- Requires fraud detection and subrogation analysis
- Subject to fair claims practices regulations

### Risk Profile
- Composite assessment of insured's risk factors
- Includes credit score, claims history, violations, property condition
- Drives underwriting decisions and pricing
- Must avoid unfair discrimination (regulatory requirement)

## Business Rules Structure

Insurance rules are organized in a tiered system:

```yaml
rule_categories:
  underwriting:
    auto_insurance:
      - driver_age_requirements       # Min age, license duration
      - vehicle_eligibility           # Age, type, modifications
      - violation_thresholds          # Points, DUI, at-fault
      - claims_history_limits         # Frequency, severity
    home_insurance:
      - property_age_limits           # Construction year
      - roof_condition_requirements   # Age, material, condition
      - occupancy_rules               # Owner-occupied vs rental
      - protection_class_minimum      # Fire station proximity

  rating:
    base_rate_calculation:
      - territory_factors             # Geography-based pricing
      - driver_factors                # Age, experience, record
      - vehicle_factors               # Make, model, safety features
      - coverage_factors              # Limits, deductibles
    discount_application:
      - multi_policy_discount         # Bundle auto + home
      - safe_driver_discount          # Clean record for N years
      - security_system_discount      # Alarm, cameras, monitoring

  compliance:
    state_requirements:
      - mandatory_coverages           # Liability minimums by state
      - rate_filing_procedures        # Prior approval vs file-and-use
      - cancellation_notice_periods   # 10-day, 30-day, 60-day
      - disclosure_requirements       # Consumer information notices
```

## How This Maps to SAGE Phases

### Early Phases: Foundation & Core Services
- Database schema for policies, claims, customers, risk profiles
- API stubs for all domain services (underwriting, rating, claims)
- Type definitions for all business entities
- Authentication framework (agent/customer portals)
- Base UI components (policy search, claim filing form)

### Middle Phases: Business Logic & Integration
- Underwriting rule engine implementation
- Rating calculation logic (base rates, factors, discounts)
- Claims processing workflow (FNOL through settlement)
- Compliance validation engine
- Integration with external rating APIs
- Unit tests for all business rules

### Late Phases: Hardening & Production Readiness
- Performance optimization (caching rate tables, query optimization)
- Security hardening (PII encryption, audit logging)
- State-specific compliance validation
- Monitoring dashboard for decision metrics
- Deployment configuration for multi-environment setup

## Performance Requirements (Insurance-Specific)

| Operation | Target | Maximum | Degraded Mode |
|-----------|--------|---------|---------------|
| Quote generation | 500ms | 2s | 5s |
| Policy issuance | 2s | 5s | 10s |
| Claims FNOL | 1s | 3s | 5s |
| Underwriting decision | 1s | 3s | Manual review |
| Rating calculation | 200ms | 500ms | Cached rates |

## Compliance Matrix Pattern

Insurance compliance varies by state. Structure compliance as a matrix:

```yaml
compliance_by_state:
  california:
    rate_approval: prior_approval      # Prop 103 requirements
    cancellation_notice: 30_days
    special_requirements:
      - FAIR_plan_availability
      - earthquake_disclosure
      - wildfire_risk_assessment

  new_york:
    rate_approval: prior_approval
    cancellation_notice: 60_days
    special_requirements:
      - Reg_187_suitability
      - DFS_cybersecurity_regulation

  florida:
    rate_approval: file_and_use
    cancellation_notice: 45_days
    special_requirements:
      - hurricane_deductible_disclosure
      - sinkhole_coverage_requirements
      - citizens_eligibility_check

  texas:
    rate_approval: file_and_use
    cancellation_notice: 30_days
    special_requirements:
      - benchmark_rate_system
      - TWIA_coastal_requirements
```

## Creating a New Domain Module

To create a domain module for a different industry, follow this structure:

```
domains/{your-domain}/
├── README.md                 # Domain overview and getting started
├── business-rules.yaml       # Rule engine configuration
├── data-models.yaml          # Entity definitions and relationships
├── compliance-matrix.yaml    # Regulatory requirements (if applicable)
├── api-specifications.yaml   # Domain-specific API definitions
└── templates/                # Starter code for common services
    ├── {service-1}/
    │   └── service-spec.yaml
    └── {service-2}/
        └── service-spec.yaml
```

### Mapping Any Domain to SAGE

| Insurance Concept | Generic Equivalent | Your Domain |
|-------------------|-------------------|-------------|
| Policy | Core business entity | {your main entity} |
| Underwriting | Risk/eligibility assessment | {your assessment process} |
| Rating | Pricing engine | {your pricing logic} |
| Claims | Event processing | {your event handling} |
| Compliance | Regulatory validation | {your compliance needs} |
| Agent/Customer portals | User-facing applications | {your user interfaces} |

This mapping ensures that the SAGE phase structure applies regardless of domain.
The phased approach (Foundation → Logic → Integration → Hardening) works because
every domain has structural scaffolding, business logic, and production concerns.
