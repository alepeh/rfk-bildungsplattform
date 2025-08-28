# RFK Bildungsplattform

## 📚 Overview

The RFK Bildungsplattform (Education Platform) is a comprehensive Django-based learning management system designed for the Burgenland Chimney Sweeper Association (Burgenländische Rauchfangkehrer). It provides a complete solution for managing training courses, registrations, certifications, and educational resources for chimney sweeper professionals.

## 🎯 Key Features

### Course Management
- **Course Creation & Scheduling**: Create and manage various types of training courses (Schulungen) with detailed descriptions, pricing tiers, and requirements
- **Training Types**: Support for different training categories (SchulungsArt) linked to professional functions
- **Course Locations**: Manage multiple training venues with complete contact information
- **Course Materials**: Upload and manage training documents and materials per course
- **Participant Limits**: Set minimum and maximum participant counts per training session

### User & Organization Management
- **Role-based Access**: Different roles for business owners (Geschäftsführer), employees, and partners
- **Business Management**: Track chimney sweeper businesses (Betriebe) with their employees
- **Function Requirements**: Link professional functions to required training certifications
- **Organization Support**: Special pricing tiers for partner organizations

### Registration & Booking
- **Public Course Catalog**: Browse upcoming training sessions with real-time availability
- **Bulk Registration**: Business owners can register multiple employees at once
- **Guest Registration**: Support for external participants without system accounts
- **Meal Preferences**: Track dietary requirements for catering purposes
- **Availability Tracking**: Real-time seat availability and overbooking prevention

### Order Management
- **Shopping Cart System**: Modern checkout flow for course bookings
- **Tiered Pricing**: Standard and discounted pricing based on organization membership
- **Order Confirmation**: Automated email confirmations with order details
- **Order History**: Users can view their past orders and registrations

### Document Management
- **Role-based Documents**: Documents restricted by professional function
- **Course Materials**: Downloadable materials linked to specific courses
- **Scaleway Object Storage**: Cloud storage integration for reliable file hosting

### Communication
- **Email Notifications**: Automated reminders for upcoming courses
- **Bulk Communications**: Send reminders to all participants of a course
- **Order Confirmations**: Automatic email receipts for bookings

### Administration
- **Django Admin Interface**: Comprehensive backend for managing all platform data
- **CSV Exports**: Export participant lists for offline processing
- **PDF Generation**: Generate attendance sheets with participant details
- **Participant Tracking**: Track attendance status (participated, excused, unexcused)

### Additional Features
- **Todo System**: Internal task management for platform improvements
- **Data Privacy**: GDPR compliance with explicit consent tracking (DSV)
- **Multi-tenant Support**: Separate test and production environments
- **Responsive Design**: Bootstrap 5-based responsive interface

## 🏗️ Architecture

### Technology Stack
- **Backend**: Django 4.2+ (Python 3.11)
- **Database**: PostgreSQL
- **Frontend**: Django Templates with Bootstrap 5
- **Storage**: Scaleway Object Storage for documents
- **Email**: Scaleway Transactional Email API
- **Deployment**: Docker containerization with Nginx reverse proxy

### Project Structure

```
rfk-bildungsplattform/
├── bildungsplattform/     # Main Django project configuration
│   ├── settings.py        # Django settings
│   ├── urls.py           # Root URL configuration
│   └── admin.py          # Admin customizations
├── core/                 # Main application
│   ├── models.py         # Data models
│   ├── views/            # View logic (separated by feature)
│   ├── templates/        # HTML templates
│   ├── services/         # Business logic (email service)
│   ├── migrations/       # Database migrations
│   └── static/           # Static assets
├── erweiterungen/        # Extensions app (todo system)
├── documents/            # Document storage
├── nginx/                # Nginx configuration
├── Dockerfile            # Container configuration
└── manage.py            # Django management script
```

### Data Models

#### Core Entities
- **Person**: Individual users (employees, business owners)
- **Betrieb**: Chimney sweeper businesses
- **Organisation**: Partner organizations with special pricing
- **Funktion**: Professional roles/functions

#### Training Entities
- **Schulung**: Training courses
- **SchulungsArt**: Training categories
- **SchulungsTermin**: Scheduled training sessions
- **SchulungsOrt**: Training locations
- **SchulungsTeilnehmer**: Course participants
- **SchulungsUnterlage**: Course materials

#### Business Entities
- **Bestellung**: Orders for course registrations
- **Document**: Platform-wide documents with access control

### Key Design Patterns

1. **Model-View-Template (MVT)**: Standard Django architecture pattern
2. **Fat Models**: Business logic encapsulated in model methods and properties
3. **Service Layer**: Separate services module for complex business logic (email)
4. **Inline Admin**: Extensive use of Django admin inlines for related data management
5. **Form Sets**: Django formsets for bulk data entry (employee management)

## 🚀 Deployment

### Docker Deployment
The application is containerized using Docker with:
- Python 3.11 slim base image
- Nginx as reverse proxy
- Static file collection during build
- Environment-based configuration

### Environment Variables
Required environment variables:
```bash
# Core Configuration
ENVIRONMENT   # Environment: development, staging, or production
DEBUG         # Debug mode (auto-disabled in production)
SECRET_KEY    # Django secret key (required in production)

# Database Configuration  
PGDATABASE    # PostgreSQL database name
PGUSER        # PostgreSQL username
PGPASSWORD    # PostgreSQL password
PGHOST        # PostgreSQL host
PGPORT        # PostgreSQL port

# External Services
SCALEWAY_EMAIL_API_TOKEN  # Email service API token
SCALEWAY_ACCESS_KEY       # Object storage access key
SCALEWAY_SECRET_KEY       # Object storage secret key
SCALEWAY_BUCKET_NAME      # Object storage bucket name
```

### Security Configuration
The application now features environment-aware security settings:

**Production Environment** (`ENVIRONMENT=production`):
- DEBUG automatically disabled
- Strict ALLOWED_HOSTS restriction
- HTTPS enforcement with SSL redirect
- Secure cookies with HTTPONLY and SAMESITE flags
- HSTS (HTTP Strict Transport Security) enabled
- XSS protection and content type sniffing prevention

**Development Environment** (`ENVIRONMENT=development`):
- DEBUG enabled by default (configurable)
- Relaxed ALLOWED_HOSTS for local testing
- Security headers appropriate for development
- Detailed error logging

**Verification**: Run `python manage.py check_security` to verify your security configuration

### Database Management
- Automatic migrations on container start
- PostgreSQL backup script included
- Model visualization with django-extensions

## 📊 Current Implementation Status

### Completed Features ✅
- Full course management system
- User registration and authentication
- Multi-tier pricing system
- Email notifications
- Order management
- Document management with access control
- Admin interface with custom actions
- PDF export for attendance lists
- Responsive web interface

### Known Limitations ⚠️
- ~~Debug mode enabled in production~~ ✅ Fixed with environment-based configuration
- ~~Broad ALLOWED_HOSTS configuration ('*')~~ ✅ Fixed with environment-specific hosts
- No payment gateway integration
- Limited reporting capabilities
- No API endpoints for external integration

## 🔧 Improvement Suggestions

### High Priority

1. **Security Enhancements** ✅ Partially Complete
   - ✅ Disable DEBUG mode in production (environment-based configuration)
   - ✅ Implement proper ALLOWED_HOSTS restriction
   - ✅ Add security headers (HSTS, XSS protection, etc.)
   - ✅ Implement HTTPS-only cookies in production
   - ⏳ Add rate limiting for authentication attempts
   - ⏳ Add Content Security Policy headers

2. **Code Organization**
   - Split large views.py into feature-specific modules ✅ (partially done)
   - Create a proper service layer for business logic
   - Implement repository pattern for data access
   - Add comprehensive logging throughout the application

3. **Testing** ✅ Complete
   - ✅ Comprehensive unit tests for models and views
   - ✅ Integration tests for critical workflows  
   - ✅ End-to-end tests for registration flow
   - ✅ Test coverage reporting and CI pipeline
   - ✅ GitHub Actions CI with automated testing

### Medium Priority

4. **API Development**
   - Implement REST API using Django REST Framework
   - Add API authentication (JWT/OAuth2)
   - Create API documentation with OpenAPI/Swagger
   - Enable mobile app integration

5. **Performance Optimization**
   - Implement database query optimization (select_related, prefetch_related)
   - Add Redis caching for frequently accessed data
   - Implement pagination for large data sets
   - Add database indexes for common queries

6. **User Experience**
   - Add advanced search and filtering
   - Implement real-time notifications
   - Add calendar integration for training schedules
   - Create a dashboard with key metrics

### Low Priority

7. **Features Enhancement**
   - Add payment gateway integration
   - Implement certificate generation
   - Add reporting and analytics module
   - Create mobile-responsive email templates
   - Add multi-language support

8. **DevOps Improvements**
   - Implement proper secrets management (e.g., HashiCorp Vault)
   - Add health check endpoints
   - Implement blue-green deployment strategy
   - Add application monitoring (e.g., Sentry)
   - Set up automated backups

9. **Code Quality**
   - Add type hints throughout the codebase
   - Implement pre-commit hooks for code formatting
   - Add docstrings to all functions and classes
   - Create developer documentation

10. **Maintainability**
    - Upgrade to latest Django LTS version
    - Implement feature flags for gradual rollouts
    - Add database migration testing
    - Create staging environment matching production

## 🛠️ Development Setup & Workflow

### Prerequisites
- Python 3.11+
- PostgreSQL
- Git
- Poetry or pip for dependency management

### Development Workflow

This project follows a **feature branch workflow** with protected main branch:

#### 1. Feature Development Process
```bash
# 1. Create a new feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# 2. Make your changes and commit regularly
git add .
git commit -m "feat: implement user authentication"

# 3. Push feature branch (triggers CI checks and staging deployment)
git push origin feature/your-feature-name

# 4. Create Pull Request to main branch
# - All CI checks must pass (tests, quality, security)
# - Requires code review and approval
# - Main branch is protected - no direct pushes allowed
```

#### 2. Branch Protection Rules
- **Main Branch**: Protected, requires PR with reviews
- **Feature Branches**: Trigger quality checks and staging deployment
- **Pull Requests**: Must pass all CI checks before merge

#### 3. Automated CI/CD Pipeline
- **Feature Branch Push**: Runs tests, quality checks, deploys to staging
- **Main Branch Merge**: Runs full test suite + E2E tests, deploys to production
- **Quality Gates**: Black formatting, isort, flake8, security scans

### Local Development Setup

1. Clone the repository
```bash
git clone https://github.com/your-org/rfk-bildungsplattform.git
cd rfk-bildungsplattform
```

2. Set up virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run migrations
```bash
python manage.py migrate
```

6. Create superuser
```bash
python manage.py createsuperuser
```

7. Run development server
```bash
python manage.py runserver
```

### Code Quality Standards

Before pushing, ensure your code meets quality standards:

```bash
# Format code
black core/ erweiterungen/ bildungsplattform/
isort core/ erweiterungen/ bildungsplattform/

# Check code quality
flake8 core/ erweiterungen/ bildungsplattform/ --max-line-length=88 --extend-ignore=E203,W503

# Run tests locally
pytest core/tests/ -v

# Security check
python manage.py check_security
```

### Generate Model Diagram
```bash
python manage.py graph_models -o bildungsplattform_model.png
```

### Database Backup
```bash
pg_dump > "backups/backup_$(date +'%Y-%m-%d_%H-%M-%S').sql"
```

## 🧪 Testing

The application includes comprehensive testing infrastructure with multiple test types:

### Test Suites

- **Unit Tests**: Test individual models, views, and utilities in isolation
- **Integration Tests**: Test complete workflows and multi-component interactions  
- **End-to-End Tests**: Test user journeys through the browser interface
- **Coverage Reporting**: Detailed code coverage analysis with HTML reports

### Running Tests

```bash
# Quick test run (unit + integration)
./scripts/test.sh fast

# Run specific test suites
./scripts/test.sh unit        # Unit tests only
./scripts/test.sh integration # Integration tests only  
./scripts/test.sh e2e         # End-to-end tests (requires Chrome)
./scripts/test.sh coverage    # Tests with coverage report

# Using pytest directly
pytest core/tests/test_models.py -v
pytest -k "test_registration" -v
```

### Coverage Reports

```bash
# Generate coverage report
./scripts/test.sh coverage

# View HTML report
open htmlcov/index.html
```

### Test Coverage Targets

- **Overall**: 80% minimum coverage
- **Models**: 95% coverage target
- **Views**: 85% coverage target  
- **Critical Business Logic**: 90% coverage target

### Continuous Integration

GitHub Actions CI pipeline runs on every pull request and push:
- Automated testing across Python 3.11 and 3.12
- Code quality checks (Black, isort, flake8)
- Security scanning (safety, bandit)
- E2E testing on main branch deployments
- Coverage reporting integration

See [Testing Guide](docs/TESTING.md) for detailed testing documentation.

## 📝 License

This project is licensed under the terms specified in the LICENSE file.

## 🤝 Contributing

Please read our contributing guidelines before submitting pull requests.

## 📞 Support

For support and questions, please contact the Burgenland Chimney Sweeper Association.

---

*Built with ❤️ for the Burgenländische Rauchfangkehrer*