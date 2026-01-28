# 🧪 Saramedico Backend Testing Guide

## Overview

This guide explains how to run and create tests for the Saramedico Backend. The test suite covers all API endpoints, end-to-end flows, and integration scenarios as specified in `prompt.md`.

---

## 📋 Test Structure

### Test Files

```
tests/
├── conftest.py                    # Test configuration and fixtures
├── test_health.py                 # Health check endpoint tests
├── test_auth_simple.py            # Basic authentication tests
├── test_complete_endpoints.py     # Comprehensive endpoint tests (NEW)
├── test_e2e_complete_flow.py      # End-to-end flow tests (NEW)
├── test_patients.py               # Patient management tests
├── test_documents.py              # Document management tests
├── test_consultations.py          # Consultation tests
├── test_audit.py                  # Audit log tests
└── test_organization.py           # Organization tests
```

### Test Coverage

The test suite covers:

✅ **Authentication**: Register, login, MFA, logout, token refresh  
✅ **Appointments**: Create, list, accept, reject, reschedule  
✅ **Permissions**: Request, grant, revoke, list, access control  
✅ **Documents**: Upload, process, list, download, status tracking  
✅ **AI Chat**: Patient chat, doctor chat with permissions  
✅ **Patients**: CRUD operations, dashboard, profile  
✅ **Doctors**: CRUD operations, dashboard, patient list  
✅ **Admin**: Organization management, user management  
✅ **Audit**: Access logs, permission logs, compliance  
✅ **Health**: Service health checks

---

## 🚀 Running Tests

### Prerequisites

Ensure the backend services are running:

```bash
# Start services
docker-compose up -d

# Verify services are healthy
docker-compose ps
```

### Run All Tests

```bash
# Inside Docker container
docker-compose exec backend pytest tests/ -v

# Or use the test script
docker-compose exec backend ./scripts/run-tests.sh
```

### Run Specific Test Files

```bash
# Health check tests
docker-compose exec backend pytest tests/test_health.py -v

# Authentication tests
docker-compose exec backend pytest tests/test_auth_simple.py -v

# Endpoint tests
docker-compose exec backend pytest tests/test_complete_endpoints.py -v

# E2E flow tests
docker-compose exec backend pytest tests/test_e2e_complete_flow.py -v
```

### Run Specific Test Classes

```bash
# Run authentication endpoint tests
docker-compose exec backend pytest tests/test_complete_endpoints.py::TestAuthenticationEndpoints -v

# Run permission flow tests
docker-compose exec backend pytest tests/test_e2e_complete_flow.py::TestPermissionFlow -v
```

### Run Specific Test Methods

```bash
# Run single test
docker-compose exec backend pytest tests/test_complete_endpoints.py::TestAuthenticationEndpoints::test_login_success -v
```

### Run with Coverage

```bash
# Generate coverage report
docker-compose exec backend pytest tests/ --cov=app --cov-report=term-missing

# Generate HTML coverage report
docker-compose exec backend pytest tests/ --cov=app --cov-report=html

# View HTML report (generated in htmlcov/index.html)
```

### Run with Different Verbosity

```bash
# Minimal output
docker-compose exec backend pytest tests/ -q

# Normal output
docker-compose exec backend pytest tests/

# Verbose output
docker-compose exec backend pytest tests/ -v

# Very verbose output
docker-compose exec backend pytest tests/ -vv
```

---

## 🔍 Understanding Test Output

### Successful Test

```
tests/test_health.py::test_health_check PASSED                           [100%]
```

### Failed Test

```
tests/test_auth.py::test_login FAILED                                    [50%]

================================= FAILURES =================================
_______________________________ test_login _________________________________

    def test_login():
        response = client.post("/api/v1/auth/login", json={...})
>       assert response.status_code == 200
E       assert 401 == 200

tests/test_auth.py:15: AssertionError
```

### Skipped Test

```
tests/test_ai.py::test_ai_chat SKIPPED (AI service not configured)      [75%]
```

---

## 📊 Test Categories

### 1. Health Check Tests

**File**: `test_health.py`

Tests all health check endpoints:

- Main health check
- Database health
- Redis health
- MinIO health

```bash
docker-compose exec backend pytest tests/test_health.py -v
```

### 2. Authentication Tests

**File**: `test_complete_endpoints.py::TestAuthenticationEndpoints`

Tests authentication flow:

- Patient registration
- Doctor registration
- Login (success and failure)
- Get current user
- Logout

```bash
docker-compose exec backend pytest tests/test_complete_endpoints.py::TestAuthenticationEndpoints -v
```

### 3. Appointment Tests

**File**: `test_complete_endpoints.py::TestAppointmentEndpoints`

Tests appointment workflow:

- Create appointment
- List appointments
- Accept appointment
- Reject appointment

```bash
docker-compose exec backend pytest tests/test_complete_endpoints.py::TestAppointmentEndpoints -v
```

### 4. Permission Tests

**File**: `test_complete_endpoints.py::TestPermissionEndpoints`

Tests permission management:

- Request permission
- Grant permission
- List permissions
- Revoke permission

```bash
docker-compose exec backend pytest tests/test_complete_endpoints.py::TestPermissionEndpoints -v
```

### 5. Document Tests

**File**: `test_complete_endpoints.py::TestDocumentEndpoints`

Tests document management:

- Upload document
- List documents
- Get document status

```bash
docker-compose exec backend pytest tests/test_complete_endpoints.py::TestDocumentEndpoints -v
```

### 6. End-to-End Flow Tests

**File**: `test_e2e_complete_flow.py`

Tests complete user journeys:

- Complete patient journey (register → upload → chat)
- Complete doctor journey (register → request access → analyze)
- Permission lifecycle (request → grant → use → revoke)
- Appointment flow (request → accept → complete)
- Cross-hospital access denial

```bash
docker-compose exec backend pytest tests/test_e2e_complete_flow.py -v
```

---

## 🛠️ Writing New Tests

### Test Structure

```python
import pytest
from httpx import AsyncClient

class TestMyFeature:
    """Test my new feature"""

    @pytest.mark.asyncio
    async def test_my_endpoint(self, client: AsyncClient, doctor_token):
        """Test description"""
        # Arrange
        data = {"key": "value"}

        # Act
        response = await client.post(
            "/api/v1/my-endpoint",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json=data
        )

        # Assert
        assert response.status_code == 200
        assert "expected_key" in response.json()
```

### Available Fixtures

From `conftest.py`:

- `engine`: Test database engine
- `db_session`: Test database session
- `client`: Async HTTP client
- `test_user`: Test doctor user
- `doctor_token`: Valid access token for test doctor
- `patient_id`: Test patient ID
- `admin_user`: Test admin user
- `admin_token`: Valid access token for admin

### Creating Custom Fixtures

```python
@pytest_asyncio.fixture
async def my_custom_fixture(db_session):
    """Create custom test data"""
    # Setup
    data = create_test_data()
    db_session.add(data)
    await db_session.commit()

    yield data

    # Teardown (optional)
    await db_session.delete(data)
    await db_session.commit()
```

---

## 🐛 Debugging Tests

### Run with Print Statements

```bash
# Enable print output
docker-compose exec backend pytest tests/test_my_test.py -v -s
```

### Run with PDB Debugger

```python
def test_my_feature():
    import pdb; pdb.set_trace()  # Debugger will stop here
    # ... rest of test
```

```bash
# Run with debugger
docker-compose exec backend pytest tests/test_my_test.py -v -s
```

### View Full Error Traceback

```bash
# Show full traceback
docker-compose exec backend pytest tests/test_my_test.py -v --tb=long

# Show short traceback
docker-compose exec backend pytest tests/test_my_test.py -v --tb=short

# Show no traceback
docker-compose exec backend pytest tests/test_my_test.py -v --tb=no
```

---

## 📈 Coverage Reports

### Generate Coverage Report

```bash
# Terminal report
docker-compose exec backend pytest tests/ --cov=app --cov-report=term-missing

# HTML report
docker-compose exec backend pytest tests/ --cov=app --cov-report=html

# XML report (for CI/CD)
docker-compose exec backend pytest tests/ --cov=app --cov-report=xml
```

### View Coverage Report

```bash
# Copy HTML report from container
docker cp saramedico_backend:/app/htmlcov ./htmlcov

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Goals

- **Overall**: >80% coverage
- **Critical paths**: >90% coverage
- **API endpoints**: 100% coverage
- **Business logic**: >85% coverage

---

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Build Docker images
        run: docker-compose build

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services
        run: sleep 30

      - name: Run tests
        run: docker-compose exec -T backend pytest tests/ -v --cov=app

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 🎯 Test Best Practices

### 1. Test Naming

```python
# Good
def test_user_can_login_with_valid_credentials():
    pass

# Bad
def test_login():
    pass
```

### 2. Arrange-Act-Assert Pattern

```python
def test_create_patient():
    # Arrange
    patient_data = {"name": "John Doe", ...}

    # Act
    response = client.post("/api/v1/patients", json=patient_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == "John Doe"
```

### 3. Test Independence

Each test should be independent and not rely on other tests:

```python
# Good - Creates its own data
def test_get_patient(db_session):
    patient = create_patient(db_session)
    response = client.get(f"/api/v1/patients/{patient.id}")
    assert response.status_code == 200

# Bad - Relies on data from another test
def test_get_patient():
    response = client.get("/api/v1/patients/1")  # Assumes patient 1 exists
    assert response.status_code == 200
```

### 4. Test One Thing

```python
# Good - Tests one specific behavior
def test_login_with_invalid_password():
    response = client.post("/api/v1/auth/login", json={
        "email": "user@test.com",
        "password": "wrong_password"
    })
    assert response.status_code == 401

# Bad - Tests multiple things
def test_authentication():
    # Tests login, logout, and token refresh all in one test
    pass
```

---

## 🚨 Common Issues

### Issue: Tests Fail with Database Connection Error

**Solution**:

```bash
# Ensure database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Issue: Tests Fail with "Table doesn't exist"

**Solution**:

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Or recreate test database
docker-compose exec postgres psql -U saramedico_user -c "DROP DATABASE IF EXISTS saramedico_test;"
docker-compose exec postgres psql -U saramedico_user -c "CREATE DATABASE saramedico_test;"
```

### Issue: Tests Hang or Timeout

**Solution**:

```bash
# Increase timeout
docker-compose exec backend pytest tests/ -v --timeout=300

# Or check for deadlocks in logs
docker-compose logs backend
```

---

## ✅ Testing Checklist

Before committing code:

- [ ] All tests pass locally
- [ ] New features have tests
- [ ] Coverage is maintained or improved
- [ ] No skipped tests without good reason
- [ ] Tests are independent and isolated
- [ ] Test names are descriptive
- [ ] No hardcoded values (use fixtures)
- [ ] Edge cases are tested
- [ ] Error cases are tested
- [ ] Documentation is updated

---

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [HTTPX Documentation](https://www.python-httpx.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

**Happy Testing! 🎉**
