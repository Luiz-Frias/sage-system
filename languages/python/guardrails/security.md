---
name: Security
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# Security Best Practices for Insurance Systems

## Overview

Security in insurance systems is paramount due to the highly sensitive nature of personal, financial, and health data. This guide provides comprehensive security patterns and practices specifically tailored for Python-based insurance applications.

## Input Validation and Sanitization

### Core Principles

```python
from pydantic import BaseModel, validator, Field
from typing import Optional
import re
import html
import bleach

class PolicyApplicationInput(BaseModel):
    """Validated input model for policy applications"""
    
    policy_number: str = Field(..., regex=r'^POL-\d{8}$')
    applicant_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    phone: Optional[str] = Field(None, regex=r'^\+?1?\d{10,14}$')
    
    @validator('applicant_name')
    def sanitize_name(cls, v):
        # Remove any HTML/script tags
        v = bleach.clean(v, tags=[], strip=True)
        # Remove non-printable characters
        v = ''.join(char for char in v if char.isprintable())
        # Validate against known patterns
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', v):
            raise ValueError('Invalid characters in name')
        return v
    
    @validator('*', pre=True)
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v
```

### File Upload Security

```python
import magic
import hashlib
from pathlib import Path

class SecureFileHandler:
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_upload(file_data: bytes, filename: str) -> tuple[bool, str]:
        """Validate uploaded files for insurance documents"""
        
        # Check file size
        if len(file_data) > SecureFileHandler.MAX_FILE_SIZE:
            return False, "File size exceeds maximum allowed"
        
        # Validate extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in SecureFileHandler.ALLOWED_EXTENSIONS:
            return False, f"File type {file_ext} not allowed"
        
        # Verify MIME type
        mime_type = magic.from_buffer(file_data, mime=True)
        allowed_mimes = {
            'application/pdf',
            'image/jpeg',
            'image/png'
        }
        if mime_type not in allowed_mimes:
            return False, f"Invalid file content type: {mime_type}"
        
        # Generate secure filename
        file_hash = hashlib.sha256(file_data).hexdigest()[:12]
        secure_filename = f"{file_hash}{file_ext}"
        
        return True, secure_filename
```

## SQL Injection Prevention

### ORM-Based Protection

```python
from sqlalchemy import create_engine, Column, String, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Query
from sqlalchemy.sql import text
import logging

Base = declarative_base()

class Policy(Base):
    __tablename__ = 'policies'
    
    policy_id = Column(String(50), primary_key=True)
    holder_id = Column(String(50), nullable=False, index=True)
    premium = Column(Numeric(10, 2), nullable=False)
    effective_date = Column(DateTime, nullable=False)

class SecureQueryBuilder:
    """Secure query builder with parameterized queries"""
    
    def __init__(self, session):
        self.session = session
        self.logger = logging.getLogger(__name__)
    
    def get_policies_by_holder(self, holder_id: str) -> list[Policy]:
        """Safe query using ORM"""
        # NEVER use string formatting for queries
        # BAD: query = f"SELECT * FROM policies WHERE holder_id = '{holder_id}'"
        
        # GOOD: Use ORM query builder
        return self.session.query(Policy).filter(
            Policy.holder_id == holder_id
        ).all()
    
    def search_policies(self, search_params: dict) -> list[Policy]:
        """Dynamic query building with safety"""
        query = self.session.query(Policy)
        
        # Safe parameter binding
        if 'min_premium' in search_params:
            query = query.filter(Policy.premium >= search_params['min_premium'])
        
        if 'holder_pattern' in search_params:
            # Use parameterized LIKE queries
            pattern = f"%{search_params['holder_pattern']}%"
            query = query.filter(Policy.holder_id.like(pattern))
        
        return query.all()
    
    def execute_raw_query_safely(self, query_template: str, params: dict):
        """When raw SQL is absolutely necessary"""
        try:
            # Use parameterized queries
            result = self.session.execute(
                text(query_template),
                params
            )
            self.logger.info(f"Executed query with params: {list(params.keys())}")
            return result
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            raise
```

## Authentication Patterns

### JWT Implementation

```python
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenConfig:
    SECRET_KEY = secrets.token_urlsafe(32)  # In production, load from secure storage
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

class TokenData(BaseModel):
    user_id: str
    role: str
    permissions: list[str]

class AuthenticationService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: TokenData) -> str:
        to_encode = data.dict()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=TokenConfig.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire, "type": "access"})
        
        return jwt.encode(
            to_encode,
            TokenConfig.SECRET_KEY,
            algorithm=TokenConfig.ALGORITHM
        )
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(
                token,
                TokenConfig.SECRET_KEY,
                algorithms=[TokenConfig.ALGORITHM]
            )
            
            # Verify token type
            if payload.get("type") != "access":
                return None
            
            return TokenData(
                user_id=payload["user_id"],
                role=payload["role"],
                permissions=payload["permissions"]
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
```

### OAuth2 Integration

```python
from authlib.integrations.requests_client import OAuth2Session
from functools import wraps
import os

class OAuth2Service:
    def __init__(self):
        self.client_id = os.environ.get('OAUTH_CLIENT_ID')
        self.client_secret = os.environ.get('OAUTH_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('OAUTH_REDIRECT_URI')
        
    def create_oauth_session(self) -> OAuth2Session:
        return OAuth2Session(
            self.client_id,
            self.client_secret,
            redirect_uri=self.redirect_uri,
            scope='openid profile email'
        )
    
    def get_authorization_url(self) -> tuple[str, str]:
        session = self.create_oauth_session()
        authorization_url, state = session.create_authorization_url(
            'https://auth.insurance-provider.com/oauth/authorize'
        )
        return authorization_url, state
    
    def exchange_code_for_token(self, code: str, state: str) -> dict:
        session = self.create_oauth_session()
        token = session.fetch_token(
            'https://auth.insurance-provider.com/oauth/token',
            authorization_response=code,
            state=state
        )
        return token
```

## PII Data Handling and Encryption

### Field-Level Encryption

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class PIIEncryption:
    def __init__(self, master_key: bytes = None):
        if master_key is None:
            master_key = os.environ.get('ENCRYPTION_MASTER_KEY', '').encode()
        
        # Derive encryption key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'insurance_pii_salt',  # In production, use unique salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key))
        self.cipher = Fernet(key)
    
    def encrypt_pii(self, data: str) -> str:
        """Encrypt PII data for storage"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_pii(self, encrypted_data: str) -> str:
        """Decrypt PII data for authorized access"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

class SecurePolicyHolder(Base):
    __tablename__ = 'policy_holders'
    
    id = Column(String(50), primary_key=True)
    # Encrypted fields
    ssn_encrypted = Column(String(500), nullable=False)
    dob_encrypted = Column(String(500), nullable=False)
    
    # Hashed fields for searching
    ssn_hash = Column(String(64), nullable=False, index=True)
    
    def __init__(self, **kwargs):
        self.encryptor = PIIEncryption()
        super().__init__(**kwargs)
    
    @property
    def ssn(self):
        return self.encryptor.decrypt_pii(self.ssn_encrypted)
    
    @ssn.setter
    def ssn(self, value):
        self.ssn_encrypted = self.encryptor.encrypt_pii(value)
        # Store searchable hash
        self.ssn_hash = hashlib.sha256(value.encode()).hexdigest()
```

### Data Masking

```python
class DataMasking:
    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """Mask SSN for display: XXX-XX-1234"""
        if len(ssn) >= 4:
            return f"XXX-XX-{ssn[-4:]}"
        return "XXX-XX-XXXX"
    
    @staticmethod
    def mask_account(account: str) -> str:
        """Mask account number for display"""
        if len(account) > 4:
            return f"****{account[-4:]}"
        return "****"
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Partially mask email address"""
        parts = email.split('@')
        if len(parts) == 2:
            name = parts[0]
            if len(name) > 2:
                masked_name = name[0] + '*' * (len(name) - 2) + name[-1]
                return f"{masked_name}@{parts[1]}"
        return email
```

## Secure Configuration Management

### Environment Configuration

```python
from pydantic import BaseSettings, validator
from typing import Optional
import os

class SecuritySettings(BaseSettings):
    # Database
    database_url: str
    database_pool_size: int = 20
    
    # Encryption
    encryption_master_key: str
    jwt_secret_key: str
    
    # OAuth
    oauth_client_id: str
    oauth_client_secret: str
    
    # Security headers
    cors_origins: list[str] = ["https://app.insurance.com"]
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
    
    @validator('encryption_master_key', 'jwt_secret_key')
    def validate_keys(cls, v):
        if len(v) < 32:
            raise ValueError('Security keys must be at least 32 characters')
        return v
    
    @validator('database_url')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError('Only PostgreSQL is supported for production')
        return v

# Secure loading with validation
settings = SecuritySettings()
```

### Secrets Management

```python
import boto3
from functools import lru_cache
import json

class SecretsManager:
    def __init__(self, region_name='us-east-1'):
        self.client = boto3.client('secretsmanager', region_name=region_name)
    
    @lru_cache(maxsize=32)
    def get_secret(self, secret_name: str) -> dict:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            # Log error securely without exposing secret details
            logging.error(f"Failed to retrieve secret: {secret_name}")
            raise
    
    def get_database_credentials(self) -> dict:
        """Get database credentials securely"""
        return self.get_secret('insurance/database/credentials')
    
    def get_api_keys(self) -> dict:
        """Get external API keys"""
        return self.get_secret('insurance/api/keys')
```

## API Security

### Rate Limiting

```python
from functools import wraps
from datetime import datetime, timedelta
import redis
from fastapi import HTTPException, Request

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def limit(self, max_requests: int = 60, window_seconds: int = 60):
        def decorator(func):
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                # Get client identifier
                client_id = request.client.host
                if hasattr(request.state, 'user_id'):
                    client_id = f"user:{request.state.user_id}"
                
                key = f"rate_limit:{client_id}:{func.__name__}"
                
                try:
                    current_count = self.redis.incr(key)
                    if current_count == 1:
                        self.redis.expire(key, window_seconds)
                    
                    if current_count > max_requests:
                        raise HTTPException(
                            status_code=429,
                            detail="Rate limit exceeded"
                        )
                    
                    return await func(request, *args, **kwargs)
                except redis.RedisError:
                    # If Redis fails, allow request but log
                    logging.error("Rate limiter Redis error")
                    return await func(request, *args, **kwargs)
            
            return wrapper
        return decorator

# Usage
rate_limiter = RateLimiter(redis.Redis())

@rate_limiter.limit(max_requests=10, window_seconds=60)
async def submit_claim(request: Request, claim_data: dict):
    # Process insurance claim
    pass
```

### CORS Configuration

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def configure_cors(app: FastAPI, settings: SecuritySettings):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Total-Count"],
        max_age=3600,
    )
```

### Security Headers

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.insurance.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://api.insurance.com"
        )
        
        return response
```

## Audit Logging

### Comprehensive Audit System

```python
from datetime import datetime
import json
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, Integer

class AuditEventType(Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    DATA_ACCESS = "DATA_ACCESS"
    DATA_MODIFICATION = "DATA_MODIFICATION"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"
    FAILED_AUTH = "FAILED_AUTH"
    POLICY_VIEWED = "POLICY_VIEWED"
    CLAIM_SUBMITTED = "CLAIM_SUBMITTED"
    PII_ACCESSED = "PII_ACCESSED"

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=False)
    event_type = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    action = Column(String(50), nullable=False)
    outcome = Column(String(20), nullable=False)  # SUCCESS, FAILURE
    details = Column(Text, nullable=True)

class AuditLogger:
    def __init__(self, session):
        self.session = session
    
    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        user_id: Optional[str] = None,
        ip_address: str = None,
        resource_type: str = None,
        resource_id: str = None,
        outcome: str = "SUCCESS",
        details: dict = None
    ):
        """Log security-relevant events"""
        audit_entry = AuditLog(
            user_id=user_id,
            ip_address=ip_address,
            event_type=event_type.value,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            details=json.dumps(details) if details else None
        )
        
        self.session.add(audit_entry)
        self.session.commit()
        
        # For critical events, also send to SIEM
        if event_type in [AuditEventType.FAILED_AUTH, AuditEventType.PII_ACCESSED]:
            self._send_to_siem(audit_entry)
    
    def _send_to_siem(self, audit_entry: AuditLog):
        """Send critical events to SIEM system"""
        # Implementation depends on SIEM provider
        pass

# Usage example
def access_policy_details(policy_id: str, user_id: str, ip_address: str):
    audit_logger = AuditLogger(session)
    
    try:
        # Access policy
        policy = session.query(Policy).filter_by(id=policy_id).first()
        
        # Log successful access
        audit_logger.log_event(
            event_type=AuditEventType.POLICY_VIEWED,
            action="VIEW_POLICY",
            user_id=user_id,
            ip_address=ip_address,
            resource_type="Policy",
            resource_id=policy_id,
            outcome="SUCCESS"
        )
        
        return policy
    except Exception as e:
        # Log failed access
        audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            action="VIEW_POLICY",
            user_id=user_id,
            ip_address=ip_address,
            resource_type="Policy",
            resource_id=policy_id,
            outcome="FAILURE",
            details={"error": str(e)}
        )
        raise
```

## Compliance with Insurance Regulations

### HIPAA Compliance (for Health Insurance)

```python
class HIPAACompliance:
    """HIPAA compliance helpers for health insurance data"""
    
    @staticmethod
    def validate_minimum_necessary(user_role: str, data_fields: list[str]) -> list[str]:
        """Implement minimum necessary standard"""
        role_permissions = {
            'claims_adjuster': ['policy_id', 'claim_amount', 'diagnosis_code'],
            'customer_service': ['policy_id', 'policy_status'],
            'medical_reviewer': ['diagnosis', 'treatment_plan', 'medical_history'],
        }
        
        allowed_fields = role_permissions.get(user_role, [])
        return [field for field in data_fields if field in allowed_fields]
    
    @staticmethod
    def encrypt_phi(data: dict) -> dict:
        """Encrypt Protected Health Information"""
        phi_fields = ['diagnosis', 'treatment', 'medical_history', 'prescription']
        encryptor = PIIEncryption()
        
        encrypted_data = data.copy()
        for field in phi_fields:
            if field in encrypted_data:
                encrypted_data[field] = encryptor.encrypt_pii(encrypted_data[field])
        
        return encrypted_data
```

### GDPR Compliance

```python
from datetime import datetime, timedelta

class GDPRCompliance:
    """GDPR compliance for EU customers"""
    
    def __init__(self, session):
        self.session = session
    
    def export_user_data(self, user_id: str) -> dict:
        """Right to data portability"""
        user_data = {
            'personal_info': self._get_personal_info(user_id),
            'policies': self._get_policies(user_id),
            'claims': self._get_claims(user_id),
            'communications': self._get_communications(user_id),
            'audit_logs': self._get_audit_logs(user_id)
        }
        
        # Log data export
        audit_logger = AuditLogger(self.session)
        audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            action="GDPR_DATA_EXPORT",
            user_id=user_id,
            resource_type="UserData",
            resource_id=user_id
        )
        
        return user_data
    
    def delete_user_data(self, user_id: str, reason: str):
        """Right to erasure (right to be forgotten)"""
        # Anonymize rather than delete for audit trail
        self._anonymize_user_data(user_id)
        
        # Log deletion request
        audit_logger = AuditLogger(self.session)
        audit_logger.log_event(
            event_type=AuditEventType.DATA_MODIFICATION,
            action="GDPR_DATA_DELETION",
            user_id=user_id,
            resource_type="UserData",
            resource_id=user_id,
            details={"reason": reason}
        )
```

### PCI DSS Compliance (for Payment Processing)

```python
class PCICompliance:
    """PCI DSS compliance for payment card data"""
    
    @staticmethod
    def tokenize_card(card_number: str) -> str:
        """Tokenize credit card for storage"""
        # Never store actual card numbers
        # Use payment processor's tokenization service
        # This is a placeholder - use actual payment processor API
        return "tok_" + hashlib.sha256(card_number.encode()).hexdigest()[:16]
    
    @staticmethod
    def mask_card_number(card_number: str) -> str:
        """Display masked card number"""
        if len(card_number) >= 4:
            return f"****-****-****-{card_number[-4:]}"
        return "****-****-****-****"
    
    @staticmethod
    def validate_cvv_not_stored(payment_data: dict) -> dict:
        """Ensure CVV is never stored"""
        prohibited_fields = ['cvv', 'cvc', 'cvv2', 'cvc2', 'security_code']
        
        for field in prohibited_fields:
            if field in payment_data:
                del payment_data[field]
        
        return payment_data
```

## Security Testing

### Security Test Suite

```python
import pytest
from unittest.mock import Mock, patch

class TestSecurityMeasures:
    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are blocked"""
        malicious_input = "'; DROP TABLE policies; --"
        
        with pytest.raises(ValueError):
            PolicyApplicationInput(
                policy_number="POL-12345678",
                applicant_name=malicious_input,
                email="test@example.com"
            )
    
    def test_xss_prevention(self):
        """Test that XSS attempts are sanitized"""
        xss_attempt = "<script>alert('XSS')</script>John Doe"
        
        input_model = PolicyApplicationInput(
            policy_number="POL-12345678",
            applicant_name=xss_attempt,
            email="test@example.com"
        )
        
        assert "<script>" not in input_model.applicant_name
        assert "alert" not in input_model.applicant_name
    
    def test_authentication_brute_force(self):
        """Test rate limiting on authentication endpoints"""
        auth_service = AuthenticationService()
        
        # Simulate multiple failed login attempts
        for i in range(10):
            result = auth_service.verify_password("wrong_password", "hashed_password")
            assert result is False
        
        # 11th attempt should be rate limited
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_password("wrong_password", "hashed_password")
        
        assert exc_info.value.status_code == 429
    
    def test_encryption_decryption(self):
        """Test PII encryption/decryption"""
        encryptor = PIIEncryption()
        sensitive_data = "123-45-6789"
        
        encrypted = encryptor.encrypt_pii(sensitive_data)
        assert encrypted != sensitive_data
        assert len(encrypted) > len(sensitive_data)
        
        decrypted = encryptor.decrypt_pii(encrypted)
        assert decrypted == sensitive_data
```

## Security Checklist

### Pre-Deployment Security Checklist

- [ ] All user inputs are validated and sanitized
- [ ] SQL queries use parameterized statements or ORM
- [ ] Authentication uses strong hashing (bcrypt/scrypt)
- [ ] JWT tokens have appropriate expiration times
- [ ] All PII is encrypted at rest
- [ ] HTTPS is enforced for all endpoints
- [ ] Security headers are properly configured
- [ ] Rate limiting is implemented on all public endpoints
- [ ] Audit logging captures all security events
- [ ] Error messages don't expose sensitive information
- [ ] Dependencies are scanned for vulnerabilities
- [ ] Secrets are stored in secure vault (not in code)
- [ ] File uploads are validated and scanned
- [ ] CORS is properly configured
- [ ] Session management is secure
- [ ] Password policy enforces strong passwords
- [ ] Multi-factor authentication is available
- [ ] Data retention policies are implemented
- [ ] Backup encryption is enabled
- [ ] Penetration testing has been performed

### Incident Response Plan

1. **Detection**: Monitor audit logs and security alerts
2. **Containment**: Isolate affected systems
3. **Investigation**: Analyze audit logs and system state
4. **Remediation**: Fix vulnerabilities and patch systems
5. **Recovery**: Restore services with enhanced security
6. **Lessons Learned**: Update security practices

## Continuous Security Monitoring

```python
class SecurityMonitor:
    """Continuous security monitoring system"""
    
    def __init__(self):
        self.alert_threshold = {
            'failed_logins': 5,
            'api_errors': 100,
            'data_access_anomaly': 50
        }
    
    async def monitor_failed_logins(self):
        """Monitor for brute force attempts"""
        # Query recent failed login attempts
        # Alert if threshold exceeded
        pass
    
    async def monitor_data_access_patterns(self):
        """Detect unusual data access patterns"""
        # Analyze access logs for anomalies
        # Alert on suspicious patterns
        pass
    
    async def monitor_api_usage(self):
        """Monitor API usage for abuse"""
        # Track API call patterns
        # Alert on unusual activity
        pass
```

This comprehensive security guide provides the foundation for building secure insurance systems in Python, addressing the unique challenges of handling sensitive financial and health data while maintaining compliance with industry regulations.