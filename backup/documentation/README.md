# 🏥 ZAIN Hospital Management System

A comprehensive, modern Hospital Management System built with Django, featuring multi-tenant architecture, advanced security, and comprehensive healthcare modules.

## ✨ Key Features

### 🔐 **Enhanced Security**
- **Two-Factor Authentication (2FA)** with TOTP and backup codes
- **Advanced Password Policies** with complexity requirements
- **Rate Limiting** and login attempt monitoring
- **Enhanced Security Headers** and CSP protection
- **Activity Logging** with comprehensive audit trails
- **Session Management** with secure configurations

### 🏢 **Multi-Tenant Architecture**
- Complete hospital isolation
- Subscription management
- Department hierarchies
- Role-based access control

### 👥 **User Management**
- Multiple user roles (Doctor, Nurse, Admin, Patient, etc.)
- Custom user profiles with medical qualifications
- Staff scheduling and availability management

### 🩺 **Clinical Modules**
- **Patient Management** - Complete medical records
- **Appointment System** - Advanced scheduling with conflicts detection
- **Emergency Management** - Triage and critical care tracking
- **Laboratory** - Test orders and results management
- **Pharmacy** - Medication management and dispensing
- **Surgery** - Surgical procedures and scheduling
- **IPD/OPD** - Inpatient and Outpatient department management

### 💰 **Financial Management**
- **Billing System** - Comprehensive invoicing
- **Insurance Integration** - Claims processing
- **Payment Tracking** - Multiple payment methods
- **Financial Reporting** - Revenue and expense analysis

### 📊 **Analytics & Reporting**
- Real-time dashboard with key metrics
- Patient flow analytics
- Financial reports
- Custom report generation
- Data export capabilities

### 🔧 **System Administration**
- **Health Monitoring** - System performance tracking
- **Automated Backups** - Database and media file backups
- **Log Management** - Centralized logging with rotation
- **Configuration Management** - Environment-based settings

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- SQLite (for development) or PostgreSQL (for production)
- Redis (optional, for caching and task queue)

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/Zain-Technologies-22/Hospital-Management-System.git
cd Hospital-Management-System

# Run the enhanced setup script
python setup_enhanced.py
```

### Option 2: Manual Setup

```bash
# Clone the repository
git clone https://github.com/Zain-Technologies-22/Hospital-Management-System.git
cd Hospital-Management-System

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env .env.local
# Edit .env.local with your settings

# Setup database
python manage.py migrate
python manage.py createcachetable
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## 📁 Project Structure

```
zain_hms/
├── apps/                          # Application modules
│   ├── accounts/                  # User authentication & hospitals
│   ├── appointments/              # Appointment scheduling
│   ├── billing/                   # Financial management
│   ├── core/                      # Core system functionality
│   ├── dashboard/                 # Main dashboard
│   ├── doctors/                   # Doctor management
│   ├── emergency/                 # Emergency services
│   ├── patients/                  # Patient records
│   ├── pharmacy/                  # Medication management
│   └── ...                       # Other modules
├── static/                        # Static files (CSS, JS, images)
├── templates/                     # HTML templates
├── media/                         # User uploaded files
├── logs/                          # Application logs
├── backups/                       # System backups
├── requirements.txt               # Python dependencies
├── .env                          # Environment configuration
└── manage.py                     # Django management script
```

## ⚙️ Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Security
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=zain_hms
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security Features
ENABLE_2FA=True
LOGIN_ATTEMPT_LIMIT=5
RATELIMIT_ENABLE=True

# Monitoring (Optional)
SENTRY_DSN=your-sentry-dsn
```

### Database Configuration

For production, update the database settings in `settings.py` to use PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}
```

## 🛡️ Security Features

### Two-Factor Authentication
Enable 2FA for enhanced security:
1. Install authenticator app (Google Authenticator, Authy)
2. Go to Profile → Security → Enable 2FA
3. Scan QR code and save backup codes

### Password Policy
- Minimum 12 characters
- Must include uppercase, lowercase, numbers, and special characters
- Cannot be similar to user information
- Cannot be a common password

### Rate Limiting
- API endpoints: 1000 requests/hour per user
- Login attempts: 5 attempts per IP before lockout
- Anonymous requests: 100 requests/hour per IP

## 📊 Monitoring & Health Checks

### Health Check Endpoints
- `/health/` - Comprehensive system health
- `/health/ready/` - Readiness check (Kubernetes)
- `/health/live/` - Liveness check (Kubernetes)

### System Monitoring
```bash
# Check system health
python manage.py system_health

# Check system health (JSON output)
python manage.py system_health --json

# Show only alerts
python manage.py system_health --alerts-only
```

### Backup Management
```bash
# Create full backup
python manage.py backup_system

# Database only
python manage.py backup_system --database-only

# With cleanup of old backups
python manage.py backup_system --cleanup --keep-days 30
```

### Log Management
```bash
# Clean old logs
python manage.py cleanup_logs --days 30

# Include database activity logs
python manage.py cleanup_logs --days 30 --activity-logs
```

## 🔧 API Documentation

The system provides RESTful APIs for all major functions:

- Authentication: `/api/auth/`
- Patients: `/api/patients/`
- Appointments: `/api/appointments/`
- Billing: `/api/billing/`
- Reports: `/api/reports/`

API documentation is available at `/api/docs/` when the server is running.

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale services
docker-compose up -d --scale web=3

# View logs
docker-compose logs -f web
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run with coverage
pip install coverage
coverage run manage.py test
coverage report
coverage html
```

## 📈 Performance Optimization

- **Database**: Optimized queries with select_related and prefetch_related
- **Caching**: Redis-based caching for frequent queries
- **Static Files**: WhiteNoise for efficient static file serving
- **API**: Pagination and filtering for large datasets
- **Background Tasks**: Celery for asynchronous processing

## 🔄 Backup & Recovery

### Automated Backups
- Daily database backups
- Weekly media file backups
- 30-day retention policy
- Backup integrity verification

### Manual Backup
```bash
# Create backup
python manage.py backup_system

# Restore from backup
python manage.py restore_backup /path/to/backup/file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📋 Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation for new features
- Use meaningful commit messages
- Ensure security best practices

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check database status
python manage.py check --database default

# Reset migrations (development only)
python manage.py migrate --fake-initial
```

**Static Files Not Loading**
```bash
# Collect static files
python manage.py collectstatic --clear

# Check static files configuration
python manage.py check --deploy
```

**Performance Issues**
```bash
# Check system health
python manage.py system_health

# Enable debug toolbar (development)
pip install django-debug-toolbar
```

## 📞 Support

- **Documentation**: See `PROJECT_STATUS.md` for detailed module information
- **Issues**: Create an issue on GitHub
- **Email**: support@zainhms.com
- **Wiki**: Check the GitHub wiki for additional documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django and Django REST Framework communities
- Bootstrap and modern web development tools
- Healthcare IT standards and best practices
- Open source security tools and libraries

---

**Built with ❤️ by Zain Technologies for better healthcare management**
