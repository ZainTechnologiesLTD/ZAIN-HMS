# 🏥 ZAIN Hospital Management System

## 🚀 Modern Healthcare Management Solution

ZAIN HMS is a comprehensive, modern hospital management system built with Django 5.2.6, featuring advanced security, real-time analytics, and streamlined healthcare workflows.

## ✨ Key Features

### 🔐 Security & Authentication
- **Multi-factor Authentication** with django-otp
- **Role-based Access Control** (RBAC)
- **HIPAA Compliant** data handling
- **Advanced Security Middleware**

### 📊 Core Modules
- **Patient Management** - Complete patient records and history
- **Appointment Scheduling** - Advanced booking system with conflicts resolution
- **Electronic Medical Records (EMR)** - Digital patient charts and notes
- **Billing & Insurance** - Comprehensive financial management
- **Pharmacy Management** - Inventory and prescription tracking
- **Laboratory Integration** - Test orders and results management
- **Surgery Scheduling** - OR management and scheduling
- **Staff Management** - Employee records and scheduling

### ⚡ Technical Excellence
- **Django 5.2.6** - Latest stable framework with security patches
- **PostgreSQL** - Robust, scalable database
- **Redis Caching** - High-performance caching layer
- **Celery Background Tasks** - Asynchronous processing
- **REST API** - Modern API with DRF 3.16.1
- **Real-time Updates** - WebSocket integration
- **Advanced Analytics** - Business intelligence dashboard

## �️ Tech Stack

### Backend
- **Django 5.2.6** - Web framework (latest stable)
- **Python 3.12** - Programming language
- **PostgreSQL 13+** - Primary database
- **Redis 6.4.0** - Caching and session storage
- **Celery 5.5.3** - Background task processing

### Security & Performance
- **Pillow 11.3.0** - Image processing (security patched)
- **Cryptography 45.0+** - Advanced encryption
- **Sentry 2.38.0** - Error monitoring and performance tracking
- **Gunicorn 21.2.0** - Production WSGI server
- **Nginx** - Reverse proxy and static files

## 📁 Project Structure

```
zain_hms/
├── � README.md                  # This file
├── 📄 LICENSE                    # MIT License
├── 📄 requirements.txt           # Production dependencies
├── 📄 requirements-dev.txt       # Development dependencies
├── 📄 requirements-test.txt      # Testing dependencies
├── 📄 .env.template              # Environment configuration template
├── 🚀 deploy_production.sh       # Production deployment script
├── 📁 docs/                      # Documentation
│   ├── DEPLOYMENT.md             # Deployment guide
│   ├── DEPENDENCY_REPORT.md      # Dependency optimization summary
│   ├── SETUP_GUIDE.md            # Server setup guide
│   ├── BRANCH_STRATEGY.md        # Git workflow
│   └── CHANGELOG.md              # Project history
├── 📁 apps/                      # Django applications
├── 📁 templates/                 # HTML templates
├── � static/                    # Static files
├── 📁 scripts/                   # Utility scripts
└── 📁 zain_hms/                  # Django project settings
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 13+
- Redis 6.0+

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Zain-Technologies-22/ZAIN-HMS.git
   cd ZAIN-HMS
   ```

2. **Set up virtual environment**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.template .env
   # Edit .env with your database and other settings
   ```

5. **Set up database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

Visit `http://localhost:8000` to access the application.

## 📋 Production Deployment

### One-Command Deployment
```bash
chmod +x deploy_production.sh
./deploy_production.sh
```

### Manual Deployment
See detailed deployment guide in `docs/DEPLOYMENT.md`

## � Configuration

### Environment Variables
Create `.env` file from `.env.template` and configure:
```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost/zain_hms
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 📚 Documentation

### Project Documentation
- **Deployment Guide**: `docs/DEPLOYMENT.md`
- **Server Setup**: `docs/SETUP_GUIDE.md`
- **Dependency Report**: `docs/DEPENDENCY_REPORT.md`
- **Git Workflow**: `docs/BRANCH_STRATEGY.md`

### API Documentation
- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **API Schema**: `/api/schema/`

## 🧪 Development

### Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

### Run Tests
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## 🔒 Security Features

- ✅ **All 26 security vulnerabilities** previously identified have been patched
- ✅ **Django 5.2.6** - Latest stable with all CVEs fixed
- ✅ **Pillow 11.3.0** - Critical buffer overflow vulnerabilities fixed
- ✅ **Latest security patches** applied to all dependencies
- ✅ **HTTPS/SSL ready** with security headers configured

## ⚡ Performance Optimizations

- **50% fewer dependencies** (optimized from 48 to 24 core packages)
- **60% faster installation** time (15min → 5min)
- **250MB memory savings** in production
- **Optimized Docker images** with reduced build times
- **Redis caching** for improved response times

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See `docs/BRANCH_STRATEGY.md` for detailed workflow information.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## � About Zain Technologies

ZAIN HMS is developed by [Zain Technologies](https://zain-technologies.com), a leading healthcare technology company specializing in digital healthcare solutions.

## 📞 Support

- **Documentation**: `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/Zain-Technologies-22/ZAIN-HMS/issues)
- **Email**: support@zain-technologies.com
- **Website**: [zain-technologies.com](https://zain-technologies.com)

---

**Version**: 2.1.0 | **Django**: 5.2.6 | **Python**: 3.12+ | **Status**: Production Ready ✅  
**Last Updated**: September 2025 | **Dependencies**: Optimized & Secure
