# Testing Documentation

## Overview

This document describes the comprehensive testing strategy for the Notarius system. The test suite covers unit tests, integration tests, security tests, performance tests, and end-to-end tests.

## Test Structure

```
apps/notarius-api/tests/
├── unit/                    # Unit tests for Django models
│   ├── test_models_minuta.py
│   ├── test_models_documento.py
│   ├── test_models_template.py
│   ├── test_models_parte.py
│   └── test_models_processo.py
├── integration/             # Integration tests for API endpoints
│   ├── test_api_minutas.py
│   ├── test_api_documentos.py
│   ├── test_api_templates.py
│   ├── test_api_partes.py
│   └── test_api_processos.py
├── security/                # Security tests for OWASP vulnerabilities
│   ├── test_security_injection.py
│   ├── test_security_auth.py
│   ├── test_security_tenant.py
│   ├── test_security_pii.py
│   └── test_security_idor.py
├── performance/             # Performance and load tests
│   ├── test_load_api.py
│   ├── test_stress_concurrent.py
│   └── test_query_performance.py
├── e2e/                     # End-to-end workflow tests
│   ├── test_workflow_complete.py
│   ├── test_workflow_multiuser.py
│   └── test_workflow_error.py
└── fixtures/                # Test fixtures and factories
    ├── factories.py
    ├── test_data.py
    └── mock_services.py
```

## Test Categories

### 1. Unit Tests

**Purpose**: Test individual Django models and their methods in isolation.

**Coverage**:
- Model creation and validation
- Model methods and properties
- Model relationships and constraints
- Model state transitions
- PII tokenization logic

**Files**:
- `tests/unit/test_models_*.py`

**Example**:
```python
def test_minuta_creation(self):
    """Test basic minuta creation."""
    minuta = MinutaFactory(
        tenant=self.tenant,
        processo=self.processo,
        created_by=self.user
    )
    
    self.assertIsNotNone(minuta.id)
    self.assertEqual(minuta.tenant, self.tenant)
    self.assertEqual(minuta.status, 'rascunho')
```

### 2. Integration Tests

**Purpose**: Test API endpoints and their interactions with the database.

**Coverage**:
- CRUD operations for all endpoints
- Authentication and authorization
- Request/response validation
- Error handling
- Pagination and filtering
- Search functionality

**Files**:
- `tests/integration/test_api_*.py`

**Example**:
```python
def test_minuta_list(self):
    """Test minuta list endpoint."""
    minuta1 = MinutaFactory(tenant=self.tenant, processo=self.processo)
    minuta2 = MinutaFactory(tenant=self.tenant, processo=self.processo)
    
    url = reverse('minuta-list')
    response = self.client.get(url)
    
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertEqual(len(response.data['results']), 2)
```

### 3. Security Tests

**Purpose**: Test for security vulnerabilities and ensure proper protection.

**Coverage**:
- SQL injection attacks
- XSS attacks
- Command injection
- LDAP injection
- XML injection
- Authentication bypass
- Authorization bypass
- PII leak detection
- Cross-tenant access prevention

**Files**:
- `tests/security/test_security_*.py`

**Example**:
```python
def test_sql_injection_minuta_corpo_md(self):
    """Test SQL injection in minuta corpo_md field."""
    for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
        data = {
            'processo': str(self.processo.id),
            'corpo_md': payload,
            'variaveis_json': {'nome': 'token_123'},
            'status': 'rascunho',
            'gerada_por': 'usuario'
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should not cause SQL injection
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### 4. Performance Tests

**Purpose**: Test system performance under various load conditions.

**Coverage**:
- API response times
- Concurrent request handling
- Database query performance
- Memory usage
- Load testing with multiple users
- Stress testing beyond capacity

**Files**:
- `tests/performance/test_*.py`

**Example**:
```python
def test_concurrent_minuta_creation(self):
    """Test concurrent minuta creation."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_minuta) for _ in range(10)]
        results = [future.result() for future in as_completed(futures)]
    
    # All requests should succeed
    self.assertEqual(len(results), 10)
    self.assertTrue(all(status_code == status.HTTP_201_CREATED for status_code in results))
```

### 5. End-to-End Tests

**Purpose**: Test complete workflows from start to finish.

**Coverage**:
- Complete minuta workflow (create → approve → finalize)
- Complete document workflow (template → minuta → final document)
- Complete parte workflow (creation → association)
- Complete processo workflow (creation → completion)
- Complete template workflow (creation → usage)
- Complete AI workflow (intent → final document)
- Multi-tenant workflows
- Error recovery workflows

**Files**:
- `tests/e2e/test_workflow_*.py`

**Example**:
```python
def test_complete_minuta_workflow(self):
    """Test complete minuta workflow from creation to finalization."""
    # Step 1: Create minuta
    response = self.client.post(url, data, format='json')
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    # Step 2: Approve minuta
    response = self.client.post(approve_url)
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # Step 3: Finalize minuta
    response = self.client.post(finalize_url)
    self.assertEqual(response.status_code, status.HTTP_200_OK)
```

## Test Fixtures

### Factories

**Purpose**: Generate test data using Factory Boy.

**Files**:
- `tests/fixtures/factories.py`

**Example**:
```python
class MinutaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Minuta
    
    tenant = factory.SubFactory(TenantFactory)
    processo = factory.SubFactory(ProcessoFactory)
    corpo_md = factory.LazyFunction(lambda: fake.text(max_nb_chars=1000))
    status = factory.fuzzy.FuzzyChoice(['rascunho', 'aprovado', 'rejeitado', 'finalizado'])
```

### Test Data

**Purpose**: Provide comprehensive test data generators and utilities.

**Files**:
- `tests/fixtures/test_data.py`

**Example**:
```python
class TestDataGenerator:
    @staticmethod
    def create_comprehensive_test_data():
        """Create comprehensive test data for all scenarios."""
        return {
            'tenants': tenants,
            'users': all_users,
            'processos': all_processos,
            'partes': all_partes,
            'minutas': all_minutas,
            'documentos': all_documentos,
            'templates': all_templates
        }
```

### Mock Services

**Purpose**: Mock external services for testing.

**Files**:
- `tests/fixtures/mock_services.py`

**Example**:
```python
class MockAIServiceManager:
    async def generate_minuta_from_intent(self, tenant_id, user_id, intent, processo_id):
        """Mock minuta generation from intent."""
        return {
            'id': 'mock-minuta-id',
            'corpo_md': f'# Minuta Gerada\n\nBaseado no intent: {intent}',
            'status': 'rascunho'
        }
```

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install -r requirements-test.txt
```

2. Set up test database:
```bash
python manage.py migrate --settings=config.settings_test
```

### Running All Tests

```bash
# Run all tests
python run_tests.py --type all --coverage --html-report --junit-report

# Run with verbose output
python run_tests.py --type all --verbose

# Run in parallel
python run_tests.py --type all --parallel

# Run with fail-fast
python run_tests.py --type all --fail-fast
```

### Running Specific Test Types

```bash
# Unit tests only
python run_tests.py --type unit --coverage

# Integration tests only
python run_tests.py --type integration --coverage

# Security tests only
python run_tests.py --type security

# Performance tests only
python run_tests.py --type performance

# End-to-end tests only
python run_tests.py --type e2e
```

### Running with Pytest Directly

```bash
# Run all tests
pytest tests/ -v --cov=apps --cov-report=html

# Run specific test file
pytest tests/unit/test_models_minuta.py -v

# Run specific test method
pytest tests/unit/test_models_minuta.py::MinutaModelTest::test_minuta_creation -v

# Run tests with specific marker
pytest tests/ -m unit -v

# Run tests in parallel
pytest tests/ -n auto -v
```

## Test Configuration

### Pytest Configuration

**File**: `pytest.ini`

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=apps
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=95
    --junitxml=test-results.xml
    --maxfail=10
    --durations=10
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    security: Security tests
    performance: Performance tests
    e2e: End-to-end tests
    slow: Slow running tests
    requires_db: Tests that require database
    requires_network: Tests that require network access
    requires_redis: Tests that require Redis
    requires_s3: Tests that require S3
    requires_ai: Tests that require AI services
    requires_pii: Tests that require PII services
    requires_lexnode: Tests that require LexNode services
```

### Test Settings

**File**: `config/settings_test.py`

```python
# Test-specific settings
DEBUG = True
SECRET_KEY = 'test-secret-key'

# Use in-memory database for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Test-specific middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Test-specific apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'apps.base',
    'apps.processos',
    'apps.partes',
    'apps.documentos',
    'apps.auditoria',
    'apps.authentication',
    'apps.financeiro',
    'apps.integracoes',
]
```

## CI/CD Integration

### GitHub Actions

**File**: `.github/workflows/test.yml`

The CI/CD pipeline includes:

1. **Lint**: Code formatting and style checks
2. **Security**: Security vulnerability scanning
3. **Unit Tests**: Fast unit tests with coverage
4. **Integration Tests**: API endpoint tests
5. **Security Tests**: OWASP vulnerability tests
6. **Performance Tests**: Load and stress tests
7. **E2E Tests**: Complete workflow tests
8. **Load Tests**: Performance under load
9. **PII Detection**: PII leak detection

### Test Reports

The CI/CD pipeline generates:

- **Coverage Reports**: HTML and XML coverage reports
- **Test Results**: JUnit XML test results
- **Load Test Results**: HTML load test reports
- **Security Reports**: Bandit, Safety, and Semgrep reports
- **PII Detection Reports**: PII leak detection results

## Test Data Management

### Test Data Isolation

- Each test runs in isolation
- Database is reset between tests
- No shared state between tests
- Proper cleanup after each test

### Test Data Generation

- Factory Boy for model instances
- Faker for realistic test data
- Mock services for external dependencies
- Comprehensive test data generators

### Test Data Cleanup

- Automatic cleanup after each test
- Database transactions for isolation
- Proper teardown of test data
- Memory cleanup for performance tests

## Performance Testing

### Load Testing

- **Concurrent Users**: 100+ concurrent users
- **Request Rate**: 1000+ requests per second
- **Response Time**: p95 < 500ms
- **Throughput**: High throughput under load

### Stress Testing

- **System Capacity**: 150% of normal capacity
- **Recovery**: System recovery after overload
- **Memory Usage**: Memory usage under stress
- **Connection Limits**: Database connection limits

### Endurance Testing

- **24-hour Operation**: Continuous operation
- **Memory Leaks**: Memory leak detection
- **Connection Leaks**: Connection leak detection
- **Resource Usage**: Long-term resource usage

## Security Testing

### OWASP Top 10

1. **Injection**: SQL, NoSQL, Command, LDAP, XML
2. **Broken Authentication**: Authentication bypass
3. **Sensitive Data Exposure**: PII leak detection
4. **XML External Entities**: XXE attacks
5. **Broken Access Control**: Authorization bypass
6. **Security Misconfiguration**: Configuration issues
7. **Cross-Site Scripting**: XSS attacks
8. **Insecure Deserialization**: Deserialization attacks
9. **Known Vulnerabilities**: Dependency vulnerabilities
10. **Insufficient Logging**: Logging and monitoring

### PII Protection

- **PII Detection**: Scan all responses for raw PII
- **Token Validation**: Validate PII tokenization
- **Hash Verification**: Verify PII hashing
- **Leak Prevention**: Prevent PII leaks in logs

## Test Metrics

### Coverage Metrics

- **Code Coverage**: 95%+ code coverage
- **Branch Coverage**: 90%+ branch coverage
- **Line Coverage**: 95%+ line coverage
- **Function Coverage**: 95%+ function coverage

### Performance Metrics

- **Response Time**: p95 < 500ms
- **Throughput**: 1000+ requests/second
- **Concurrent Users**: 100+ concurrent users
- **Memory Usage**: < 1GB under load

### Security Metrics

- **Vulnerability Count**: 0 critical vulnerabilities
- **PII Leaks**: 0 PII leaks detected
- **Security Score**: A+ security rating
- **Compliance**: 100% compliance with security standards

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure test database is running
2. **Dependencies**: Install all test dependencies
3. **Environment Variables**: Set required environment variables
4. **Permissions**: Ensure proper file permissions

### Debug Mode

```bash
# Run tests with debug output
pytest tests/ -v -s --tb=long

# Run specific test with debug
pytest tests/unit/test_models_minuta.py::MinutaModelTest::test_minuta_creation -v -s --tb=long

# Run with pdb debugger
pytest tests/ --pdb
```

### Test Isolation

```bash
# Run tests in isolation
pytest tests/ --forked

# Run tests with fresh database
pytest tests/ --reuse-db --create-db
```

## Best Practices

### Test Writing

1. **Clear Test Names**: Descriptive test method names
2. **Single Responsibility**: One assertion per test
3. **Test Data**: Use factories for test data
4. **Isolation**: Tests should be independent
5. **Cleanup**: Proper cleanup after tests

### Test Organization

1. **Logical Grouping**: Group related tests
2. **Test Categories**: Use appropriate test categories
3. **Test Markers**: Use pytest markers for categorization
4. **Test Fixtures**: Reuse test fixtures
5. **Test Data**: Centralize test data generation

### Performance

1. **Fast Tests**: Keep unit tests fast
2. **Parallel Execution**: Use parallel execution for slow tests
3. **Test Data**: Minimize test data size
4. **Database**: Use in-memory database for unit tests
5. **Mocking**: Mock external dependencies

### Security

1. **Input Validation**: Test all input validation
2. **Authentication**: Test authentication flows
3. **Authorization**: Test authorization checks
4. **PII Protection**: Test PII protection
5. **Vulnerability Scanning**: Regular vulnerability scanning

## Conclusion

This comprehensive testing strategy ensures the Notarius system is robust, secure, and performant. The test suite covers all aspects of the system from unit tests to end-to-end workflows, providing confidence in the system's reliability and security.

For questions or issues with testing, please refer to the troubleshooting section or contact the development team.
