# Comprehensive Testing Strategy

This document outlines the comprehensive testing strategy implemented for the Notarius monorepo, covering all services, packages, and integration scenarios.

## Overview

The testing strategy follows a pyramid approach with multiple layers:

1. **Unit Tests** - Individual components and functions
2. **Integration Tests** - Cross-service communication
3. **End-to-End Tests** - Complete workflows
4. **Security Tests** - Vulnerability and injection testing
5. **Performance Tests** - Load and stress testing
6. **Quality Assurance** - Linting, type checking, and code quality

## Test Structure

```
notarius/
├── apps/
│   ├── notarius-api/
│   │   └── tests/
│   │       ├── unit/           # Unit tests for models, views, services
│   │       ├── integration/    # API integration tests
│   │       ├── security/       # Security vulnerability tests
│   │       ├── performance/    # Load and performance tests
│   │       └── e2e/           # End-to-end workflow tests
│   ├── lexnode-api/
│   │   └── tests/
│   │       ├── test_api_endpoints.py
│   │       └── test_services.py
│   ├── intent-engine/
│   │   └── tests/
│   │       ├── test_api_endpoints.py
│   │       └── test_services.py
│   └── pii-vault/
│       └── tests/
│           └── test_api_endpoints.py
├── packages/
│   ├── core/
│   │   └── tests/
│   │       ├── test_models.py
│   │       ├── test_enums.py
│   │       └── test_exceptions.py
│   ├── observability/
│   │   └── tests/
│   │       ├── test_correlation.py
│   │       └── test_logging.py
│   └── pii/
│       └── tests/
│           ├── test_extractors.py
│           ├── test_validators.py
│           └── test_morph_engine.py
└── tests/
    ├── conftest.py
    ├── test_integration.py
    └── test_e2e.py
```

## Test Categories

### 1. Unit Tests

#### Notarius API (Django)
- **Models**: Test model creation, validation, relationships
- **Views**: Test API endpoints, serializers, permissions
- **Services**: Test business logic, document processing
- **Admin**: Test admin interface functionality

#### LexNode API (FastAPI)
- **API Endpoints**: Test all REST endpoints
- **Services**: Test crawler, normalizer, indexer, retrieval
- **Error Handling**: Test error responses and edge cases

#### Intent Engine (FastAPI)
- **API Endpoints**: Test intent parsing, draft generation
- **Services**: Test AI integration, PII extraction
- **Validation**: Test intent validation and error handling

#### PII Vault (FastAPI)
- **API Endpoints**: Test PII storage, retrieval, tokenization
- **Services**: Test encryption, tokenization, morphing
- **Security**: Test PII protection mechanisms

#### Shared Packages
- **Core**: Test models, enums, exceptions
- **Observability**: Test logging, correlation, metrics
- **PII**: Test extractors, validators, morph engine

### 2. Integration Tests

#### Cross-Service Communication
- **Notarius ↔ LexNode**: Legal citation retrieval
- **Notarius ↔ Intent Engine**: Intent parsing and draft generation
- **Notarius ↔ PII Vault**: PII storage and tokenization
- **Service Discovery**: Service registration and health checks

#### Error Handling
- **Service Unavailable**: Test circuit breaker patterns
- **Timeout Handling**: Test timeout and retry mechanisms
- **Partial Failures**: Test graceful degradation

#### Data Flow
- **PII Flow**: Test PII extraction → tokenization → storage → retrieval
- **Document Flow**: Test intent → draft → validation → finalization
- **Legal Flow**: Test citation retrieval → grounding → validation

### 3. End-to-End Tests

#### Complete Workflows
- **Procuração Workflow**: Intent → PII extraction → Draft → Finalization
- **Certidão Workflow**: Intent → PII extraction → Draft → Finalization
- **Testamento Workflow**: Intent → PII extraction → Draft → Finalization

#### Error Recovery
- **Service Failure Recovery**: Test recovery from service failures
- **Partial Failure Handling**: Test workflows with partial failures
- **Timeout Recovery**: Test recovery from timeout errors

#### Performance
- **Load Testing**: Test under concurrent user load
- **Memory Usage**: Test memory consumption patterns
- **Response Times**: Test end-to-end response times

### 4. Security Tests

#### Injection Testing
- **SQL Injection**: Test database query injection
- **XSS Testing**: Test cross-site scripting vulnerabilities
- **Command Injection**: Test command execution vulnerabilities

#### PII Protection
- **PII Leakage**: Test PII exposure in logs and responses
- **Tokenization**: Test PII tokenization effectiveness
- **Encryption**: Test PII encryption and decryption

#### Authentication & Authorization
- **API Security**: Test API endpoint security
- **RBAC**: Test role-based access control
- **Session Management**: Test session security

### 5. Performance Tests

#### Load Testing
- **Concurrent Users**: Test with multiple concurrent users
- **Request Volume**: Test high request volumes
- **Response Times**: Test response time under load

#### Stress Testing
- **Memory Usage**: Test memory consumption patterns
- **CPU Usage**: Test CPU utilization
- **Database Performance**: Test database query performance

#### Scalability
- **Horizontal Scaling**: Test service scaling
- **Database Scaling**: Test database performance
- **Cache Performance**: Test caching effectiveness

## Test Execution

### Running All Tests

```bash
# Run all tests
python tests/run_all_tests.py --all

# Run quick tests (unit + linting)
python tests/run_all_tests.py --quick

# Run specific services
python tests/run_all_tests.py --services notarius lexnode

# Run specific test types
python tests/run_all_tests.py --test-types unit integration
```

### Running Individual Test Suites

```bash
# Notarius API tests
cd apps/notarius-api
python manage.py test

# LexNode API tests
cd apps/lexnode-api
pytest tests/ -v

# Intent Engine tests
cd apps/intent-engine
pytest tests/ -v

# PII Vault tests
cd apps/pii-vault
pytest tests/ -v

# Package tests
cd packages/core
pytest tests/ -v

# Integration tests
pytest tests/test_integration.py -v

# E2E tests
pytest tests/test_e2e.py -v
```

### Test Configuration

#### Pytest Configuration
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    security: Security tests
    performance: Performance tests
```

#### Django Test Configuration
```python
# settings/test.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use in-memory cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

## Test Data Management

### Fixtures
- **Factory Boy**: Generate test data for Django models
- **Faker**: Generate realistic test data
- **Mock Services**: Mock external service dependencies

### Test Database
- **In-Memory SQLite**: Fast test execution
- **Test Data Seeding**: Consistent test data
- **Database Isolation**: Each test gets clean database

### Mock Services
- **AI Services**: Mock OpenAI and other AI providers
- **External APIs**: Mock external service calls
- **File System**: Mock file operations

## Continuous Integration

### GitHub Actions
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: python tests/run_all_tests.py --all
```

### Test Reports
- **Coverage Reports**: Code coverage analysis
- **Performance Reports**: Performance metrics
- **Security Reports**: Security scan results

## Quality Metrics

### Code Coverage
- **Target**: 90%+ code coverage
- **Critical Paths**: 100% coverage for critical business logic
- **PII Handling**: 100% coverage for PII processing

### Performance Benchmarks
- **Response Time**: < 2 seconds for API endpoints
- **Throughput**: > 100 requests/second
- **Memory Usage**: < 500MB per service

### Security Standards
- **OWASP Compliance**: Follow OWASP security guidelines
- **PII Protection**: Zero PII leakage in logs
- **Input Validation**: All inputs validated and sanitized

## Test Maintenance

### Regular Updates
- **Test Data**: Update test data regularly
- **Dependencies**: Keep test dependencies updated
- **Coverage**: Monitor and improve test coverage

### Test Documentation
- **Test Cases**: Document all test scenarios
- **Edge Cases**: Document edge case testing
- **Performance**: Document performance expectations

### Test Review
- **Code Review**: Include tests in code reviews
- **Test Quality**: Review test quality and coverage
- **Test Strategy**: Regular review of testing strategy

## Troubleshooting

### Common Issues
- **Test Failures**: Check test data and mock configurations
- **Performance Issues**: Monitor resource usage and bottlenecks
- **Integration Issues**: Verify service dependencies and configurations

### Debugging
- **Test Logs**: Enable detailed test logging
- **Mock Debugging**: Debug mock service responses
- **Database Issues**: Check test database setup

### Best Practices
- **Test Isolation**: Ensure tests don't depend on each other
- **Test Data**: Use consistent and realistic test data
- **Mock Services**: Mock external dependencies appropriately
- **Error Testing**: Test both success and failure scenarios
