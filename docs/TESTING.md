# Testing Guide

This document provides comprehensive information about testing the RFK Bildungsplattform.

## 🏗️ Test Architecture

The testing strategy follows a three-tier approach:

### 1. Unit Tests (`test_models.py`, `test_views.py`)
- **Purpose**: Test individual components in isolation
- **Coverage**: Models, view functions, utilities, services
- **Speed**: Fast execution (< 1 second per test)
- **Database**: Uses test database with transactions

### 2. Integration Tests (`test_integration.py`)
- **Purpose**: Test complete user workflows
- **Coverage**: Multi-step processes, API interactions, business logic
- **Speed**: Medium execution (1-5 seconds per test)
- **Database**: Uses test database with realistic data

### 3. End-to-End Tests (`test_e2e.py`)
- **Purpose**: Test complete user journeys through the browser
- **Coverage**: UI interactions, JavaScript functionality, user flows
- **Speed**: Slow execution (10-30 seconds per test)
- **Requirements**: Chrome/Chromium browser

## 🚀 Quick Start

### Installation

```bash
# Install testing dependencies
pip install -r requirements-test.txt

# Ensure you have Chrome installed for E2E tests
# Ubuntu: sudo apt-get install google-chrome-stable
# macOS: brew install --cask google-chrome
```

### Running Tests

```bash
# Run all fast tests (recommended for development)
./scripts/test.sh fast

# Run specific test suites
./scripts/test.sh unit        # Unit tests only
./scripts/test.sh integration # Integration tests only
./scripts/test.sh e2e         # End-to-end tests only
./scripts/test.sh coverage    # Tests with coverage report
./scripts/test.sh all         # All tests (slow)

# Using pytest directly
pytest core/tests/test_models.py -v      # Specific test file
pytest -k "test_create_person" -v       # Specific test by name
pytest --lf                             # Run last failed tests only
pytest --tb=short                       # Shorter traceback format
```

## 📊 Coverage Reports

### Generating Coverage

```bash
# Generate HTML coverage report
./scripts/test.sh coverage

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Targets

- **Minimum**: 80% overall coverage
- **Models**: 95% coverage (high-value, low-complexity)
- **Views**: 85% coverage (business logic)
- **Services**: 90% coverage (critical functionality)

### Coverage Configuration

Coverage settings are in `.coveragerc`:
- Excludes: migrations, tests, settings, virtual environments
- Ignores: debug code, type checking imports, `__repr__` methods

## 🧪 Test Categories

### Model Tests

**File**: `core/tests/test_models.py`

Tests Django models including:
- Model creation and validation
- Model methods and properties
- Relationships and foreign keys
- Constraints and business rules
- String representations

**Example**:
```python
def test_schulungstermin_freie_plaetze(self):
    termin = SchulungsTermin.objects.create(
        datum_von=timezone.now(),
        datum_bis=timezone.now() + timedelta(hours=4),
        schulung=schulung,
        max_teilnehmer=10
    )
    assert termin.freie_plaetze == 10
```

### View Tests

**File**: `core/tests/test_views.py`

Tests Django views including:
- URL routing and access control
- Authentication and permissions
- Form processing and validation
- Context data and template rendering
- HTTP status codes and redirects

**Example**:
```python
def test_checkout_view_with_organisation_discount(self):
    self.client.login(username='testuser', password='testpass')
    response = self.client.get(reverse('checkout', args=[self.termin.id]))
    assert response.status_code == 200
    assert response.context['preis'] == Decimal("100.00")  # Discounted
```

### Integration Tests

**File**: `core/tests/test_integration.py`

Tests complete workflows including:
- Multi-step user journeys
- Cross-model interactions
- Complex business processes
- Email sending and external services
- Database consistency across operations

**Example Workflows**:
- Complete course registration (browse → checkout → confirm)
- Business owner employee management
- Course capacity management
- User training history tracking

### End-to-End Tests

**File**: `core/tests/test_e2e.py`

Tests browser-based user interactions:
- Full user journeys through web interface
- JavaScript functionality
- Responsive design
- Form submissions and validations
- Real browser rendering

**Requirements**:
- Chrome/Chromium browser
- selenium webdriver
- Live server (StaticLiveServerTestCase)

## 🔧 Test Configuration

### Environment Variables

Tests use specific environment settings:

```bash
ENVIRONMENT=test
DEBUG=False
SECRET_KEY=test-secret-key-for-testing-only
PGDATABASE=test_bildungsplattform
```

### Test Database

- PostgreSQL for integration/E2E tests (matches production)
- SQLite for unit tests (faster)
- Automatic cleanup after each test
- Transaction rollback for isolation

### pytest Configuration

**File**: `pytest.ini`

Key settings:
- Database reuse for faster execution
- No migrations during tests
- Coverage reporting
- Custom test discovery patterns
- Environment variable injection

## 🏃‍♂️ Running Tests Locally

### Development Workflow

1. **Write failing test first** (TDD approach)
2. **Run specific test** to verify it fails
3. **Implement feature** to make test pass
4. **Run related tests** to check for regressions
5. **Run coverage** to ensure adequate testing

### Fast Development Loop

```bash
# Run only related tests during development
pytest core/tests/test_models.py::TestSchulung -v

# Watch mode (with external tool like pytest-watch)
ptw core/tests/test_models.py

# Run tests on file change (using entr)
find . -name "*.py" | entr -c pytest core/tests/test_models.py
```

### Pre-commit Testing

```bash
# Before committing, run fast test suite
./scripts/test.sh fast

# For important features, run full suite
./scripts/test.sh all
```

## 🔄 Continuous Integration

### GitHub Actions

**File**: `.github/workflows/ci.yml`

The CI pipeline runs:

1. **Code Quality**: Black, isort, flake8
2. **Security Scan**: safety, bandit
3. **Unit & Integration Tests**: Multiple Python versions
4. **E2E Tests**: Chrome browser on main branch
5. **Coverage Reporting**: Codecov integration
6. **Deployment**: Staging and production (on specific branches)

### Pipeline Triggers

- **Pull Requests**: Full test suite + code quality
- **Main Branch**: Full suite + E2E tests + deployment
- **Develop Branch**: Full suite + staging deployment

### Artifacts

- Test results (JUnit XML)
- Coverage reports (HTML)
- Failed test screenshots (E2E)

## 🐛 Debugging Tests

### Common Issues

1. **Database State**: Tests failing due to data pollution
   ```bash
   pytest --create-db  # Force fresh database
   ```

2. **Timing Issues**: E2E tests failing due to async operations
   ```python
   WebDriverWait(driver, 10).until(
       EC.element_to_be_clickable((By.ID, "submit-btn"))
   )
   ```

3. **Missing Dependencies**: Import errors in tests
   ```bash
   pip install -r requirements-test.txt
   ```

### Debugging Tools

- **pytest --pdb**: Drop into debugger on failure
- **pytest --lf**: Run only last failed tests
- **pytest --tb=long**: Full traceback information
- **pytest -s**: Don't capture stdout (see print statements)
- **pytest --log-cli-level=DEBUG**: Show Django debug logs

### Browser Testing Debug

```bash
# Run E2E tests with visible browser (remove headless)
# Edit test_e2e.py and comment out headless option
pytest core/tests/test_e2e.py::CourseRegistrationE2ETest::test_complete_registration_workflow -s
```

## 📝 Writing New Tests

### Test Naming Convention

```python
class TestModelName:
    def test_action_expected_result(self):
        # Test implementation
```

### Test Structure (AAA Pattern)

```python
def test_example(self):
    # Arrange: Set up test data
    user = User.objects.create_user(username='test')
    
    # Act: Perform the action
    result = some_function(user)
    
    # Assert: Verify the result
    assert result.success is True
```

### Test Data Creation

Use factories for consistent test data:

```python
# Use model_bakery for quick model creation
from model_bakery import baker

schulung = baker.make(Schulung, name='Test Course')
person = baker.make(Person, vorname='Max', nachname='Test')
```

### Mock External Services

```python
from unittest.mock import patch

@patch('core.services.email.send_email')
def test_order_confirmation_email(mock_send_email):
    # Test logic
    mock_send_email.assert_called_once()
```

## 🎯 Best Practices

### Do's ✅

- **Test behavior, not implementation**
- **Use descriptive test names**
- **Keep tests simple and focused**
- **Mock external dependencies**
- **Test edge cases and error conditions**
- **Use factories for test data**
- **Clean up after tests (automatic with transactions)**

### Don'ts ❌

- **Don't test Django's functionality** (e.g., ORM behavior)
- **Don't create complex test hierarchies**
- **Don't test multiple things in one test**
- **Don't hardcode paths or URLs**
- **Don't leave commented-out test code**
- **Don't skip tests without good reason**

### Performance Tips

1. **Use transactions** instead of truncation
2. **Reuse database** between test runs  
3. **Mock external services** (email, APIs)
4. **Use minimal test data** 
5. **Run unit tests frequently**, integration tests less often
6. **Parallelize tests** when possible (`pytest -n auto`)

## 📚 Resources

### Documentation

- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [pytest Documentation](https://docs.pytest.org/)
- [Selenium WebDriver Documentation](https://selenium-python.readthedocs.io/)

### Tools

- **pytest**: Primary test runner
- **coverage**: Code coverage measurement
- **selenium**: Browser automation
- **model-bakery**: Test data factories
- **responses**: HTTP mocking
- **freezegun**: Time mocking

### Further Reading

- [Test-Driven Development with Python](https://www.obeythetestinggoat.com/)
- [Effective Python Testing](https://realpython.com/pytest-python-testing/)
- [Django Testing Best Practices](https://django-testing-docs.readthedocs.io/)

---

Happy Testing! 🧪✨