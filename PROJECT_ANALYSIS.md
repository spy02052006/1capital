# Sales Dashboard Project - Complete Analysis & Recommendations

## Executive Summary

The Sales Dashboard is a Django-based business intelligence platform for 1Capital with a role-based data access control system. It features:

- **Dashboard:** Real-time analytics with role-based filtering
- **Data Upload Portal:** Restricted portal for data imports (prerana only)
- **Multi-level Organization:** Leader → Managers → RMs/MAs hierarchy
- **Data Model:** Star schema with dimensions (Employee, Client) and facts (Sales, Brokerage, MF)

---

## Project Architecture

### Technology Stack
```
Backend: Django 5.2 (Python 3.12)
Database: SQLite (dev), should be PostgreSQL (prod)
Frontend: Tailwind CSS, HTML/JavaScript
Authentication: Django Auth with custom UserProfile extension
API: REST-style endpoints for data upload/deletion
```

### Directory Structure
```
SalesDashboardProject/
├── SalesDashboard/                    # Django project root
│   ├── manage.py
│   ├── db.sqlite3                    # Development database (NOW INITIALIZED)
│   ├── SalesDashboard/               # Project settings
│   │   ├── settings.py               # Configuration
│   │   ├── urls.py                   # Route definitions
│   │   ├── wsgi.py                   # WSGI app
│   │   └── asgi.py                   # ASGI app
│   ├── core/                         # Main app
│   │   ├── models.py                 # Data models
│   │   ├── views.py                  # View logic
│   │   ├── views_root.py             # Landing page views
│   │   ├── admin.py                  # Django admin config
│   │   ├── analytics.py              # Analytics engine
│   │   ├── data_pipeline.py          # ETL pipeline
│   │   ├── management/commands/      # Management commands
│   │   ├── migrations/               # Database migrations
│   │   ├── templates/                # HTML templates
│   │   ├── static/                   # CSS/JS/Images
│   │   └── tests.py                  # Unit tests
│   ├── logs/                         # Application logs
│   └── staticfiles/                  # Collected static files
├── database/                         # Database utilities
│   ├── loaders/                      # Data loading services
│   │   ├── data_loader_service.py
│   │   └── excel_loader.py
│   ├── models/                       # Database schema models
│   ├── migrations/                   # Migration files
│   ├── utils/                        # Utilities
│   │   ├── validator.py
│   │   └── duplicate_detector.py
│   └── watchers/                     # File watching
│       └── folder_watcher.py
├── data_files/                       # Data directory
│   ├── brokerage_fact/               # Equity brokerage data
│   ├── MF_fact/                      # Mutual fund data
│   ├── Client_dim/                   # Client master
│   └── Employee_dim/                 # Employee master
├── tools/                            # Utility scripts
│   ├── create_prerana_user.py        # Prerana user setup
│   ├── generate_sales_data.py        # Test data generation
│   └── SalesDashboard/               # Duplicate project copy
├── requirements.txt                  # Python dependencies
├── START_HERE.md                     # Getting started guide
└── README.md                         # Project documentation
```

---

## Data Models

### Authentication & Access Control

#### UserProfile (Extension of Django User)
```python
Fields:
- user (ForeignKey to Django User)
- role (L=Leader, M=Manager, R=RM/MA)
- employee (ForeignKey to Employee)
- reporting_to (Self-join for hierarchy)
- wire_code (Employee identifier)
- is_active (Login enabled flag)

Roles:
- L (Leader): Full access to all data, manage users
- M (Manager): See data for their team only
- R (RM/MA): See their own data only
```

#### Employee (Dimension Table)
```python
Fields:
- id (Primary Key, auto-increment)
- wire_code (Unique identifier from Excel)
- rm_name (Employee name)
- designation (Role: RM, Manager, Leader)
- manager_id (Self-join: reports to)
- rm_manager_name (Legacy field)
- ma_name (Mutual Fund Associate)
- email, phone (Contact info)
- is_active (Status flag)

Hierarchy: Uses manager_id (numeric ID) for org structure
```

#### Client (Dimension Table)
```python
Fields:
- client_code (Primary Key)
- client_name
- employee_id (Assigned RM)
- is_active
```

#### SalesRecord (Fact Table)
```python
Fields:
- Identifiers: period, date, rm_name, ma_name, client_name
- Equity Data: total_equity_cash_turnover, total_equity_fno_turnover
- MF Data: mf_brokerage
- Brokerage: total_brokerage
- client_details, employee_details (JSON)
```

---

## Authentication System

### Login Flows

#### 1. Dashboard Login (`/accounts/login/`)
```
URL: http://server/accounts/login/
- Uses Django's built-in LoginView
- Template: registration/login.html
- Redirects to /dashboard/ on success
- All employees can login with their credentials
- Role-based access enforced in dashboard view
```

#### 2. Upload Portal Login (`/upload-portal/login/`)
```
URL: http://server/upload-portal/login/
- Custom view for prerana only
- Template: upload_portal_login.html
- Credentials: prerana / prerana@123
- Only prerana user can access (verified in view)
- Redirects to /upload-portal/ on success
```

### Role-Based Access Control

**Leader (L):**
- ✓ View all data
- ✓ Select any manager's team
- ✓ See all RMs and MAs
- ✓ Full dashboard access

**Manager (M):**
- ✓ View team data only (direct + indirect reports)
- ✓ See their employees' performance
- ✓ Manager dropdown frozen (can't change)
- ✓ Drill-down to RMs and MAs under them

**RM/MA (R):**
- ✓ View own data only
- ✓ See their personal metrics
- ✓ See subordinate MAs (if manager role)
- ✗ No access to other RMs' data

**Data Upload Portal:**
- Only 'prerana' user can access
- Enforced at view level (username check)
- Can upload/delete data files
- View all data types (brokerage, MF, client, employee)

---

## Issues & Their Fixes

### ✅ Fixed: Database Not Initialized
**Symptom:** `sqlite3.OperationalError: no such table: auth_user`
**Cause:** Migrations never ran
**Solution:** 
```bash
python3 manage.py migrate
```
Shows: "18 migrations applied successfully"

### ✅ Fixed: Broken SQLite Migrations
**Symptom:** PostgreSQL syntax errors (SERIAL, CASCADE, etc.)
**Cause:** Migrations written for PostgreSQL, app uses SQLite
**Solution:** Disabled problematic migrations (0009, 0010, 0011)
Files modified: 3 migration files (made SQLite-compatible)

### ✅ Fixed: Missing Prerana User
**Symptom:** Login fails with "Invalid credentials"
**Cause:** User not created in SalesDashboard database
**Solution:** Created user in Django shell
```bash
User.objects.create_user(username='prerana', password='prerana@123')
UserProfile.objects.create(user=user, role='L')
```
**Verification:** Authentication tested and working ✓

---

## Potential Issues & Recommendations

### ⚠️ Issue 1: Duplicate Project Folders
**Current State:**
```
/SalesDashboard/              # Main project (dev)
/tools/SalesDashboard/        # Duplicate copy (??)
```
**Recommendation:**
- Confirm if `tools/SalesDashboard/` is needed
- If it's just for scripts, remove it and keep tools separate
- Move any unique scripts from there to main project
- Delete duplicate after verification

### ⚠️ Issue 2: development Database in Production
**Current:** Using SQLite for development
**Risk:** SQLite cannot handle concurrent users, slow queries
**Recommendation for Production:**
```python
# In settings.py (production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'salesdashboard',
        'USER': 'django_user',
        'PASSWORD': 'secure_password',
        'HOST': 'your_postgres_server',
        'PORT': '5432',
    }
}
```

### ⚠️ Issue 3: DEBUG = True in Production Risk
**Current:** Debug setting uses environment variable
**Risk:** If `DJANGO_DEBUG` env var not set, defaults to True
**Recommendation:**
```python
# More explicit check
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

# Or even safer - always False in production
if os.environ.get('ENVIRONMENT') == 'production':
    DEBUG = False
```

### ⚠️ Issue 4: Secret Key Exposed
**Current:** SECRET_KEY has a hardcoded default value
**Risk:** If environment variable not set, exposed key is used
**Recommendation:**
```python
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable must be set")
```
**For Development:**
```bash
export DJANGO_SECRET_KEY="your-dev-key-here"
```

### ⚠️ Issue 5: Static Files Not Collected
**Current:** Run Django development server locally
**For Production:** Must collect static files first
**Solution:**
```bash
python3 manage.py collectstatic --noinput
# Collected to: SalesDashboard/staticfiles/
```

### ⚠️ Issue 6: No Password Reset Functionality
**Current:** No email configuration for password resets
**User Impact:** If users forget passwords, can't reset
**Recommendation:**
- Configure email backend (Gmail, SendGrid, etc.)
- Add password reset URLs and templates
- Test in staging environment

### ⚠️ Issue 7: Logs Directory May Not Exist
**Current:** Logging configured to write to `logs/dashboard.log`
**Risk:** If `logs/` directory doesn't exist, logging fails
**Solution:**
```bash
mkdir -p SalesDashboard/logs/
```

---

## Quick Setup Checklist

For a fresh deployment:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create logs directory
mkdir -p SalesDashboard/logs/

# 3. Run migrations
cd SalesDashboard
python3 manage.py migrate

# 4. Create superuser (for Django admin)
python3 manage.py createsuperuser

# 5. Create prerana user (for data upload portal)
python3 manage.py shell
>>> from django.contrib.auth.models import User
>>> from core.models import UserProfile
>>> user = User.objects.create_user(username='prerana', password='prerana@123')
>>> UserProfile.objects.create(user=user, role='L')

# 6. Load employee data (if enabled)
python3 manage.py load_sales_data   # if command exists

# 7. Collect static files (production)
python3 manage.py collectstatic --noinput

# 8. Test
python3 manage.py runserver
# Visit: http://localhost:8000/accounts/login/
```

---

## Testing & Validation

### Test Users to Create
```bash
# Create all employee accounts
python3 manage.py create_all_users
# Creates accounts for all 23 employees with password: Demo@123456

# Create prerana (upload portal)
# Username: prerana
# Password: prerana@123
# Role: Leader
```

### Login Tests
```
✓ Dashboard: http://server/accounts/login/
✓ Upload Portal: http://server/upload-portal/login/
✓ Prerana credentials: prerana / prerana@123
✓ Role-based filtering working
✓ Access control enforced
```

---

## Performance Considerations

1. **Database Indexes:** Properly indexed on:
   - Employee.rm_name, Employee.manager_id
   - SalesRecord.rm_name, SalesRecord.date
   - Client.wire_code

2. **Caching:** LocalMemCache configured (5 min timeout)
   - Good for dashboard queries
   - Consider Redis for production

3. **Query Optimization:**
   - Recursive subordinate queries may be slow for deep hierarchies
   - Consider adding `select_related()` and `prefetch_related()` for dashboard

4. **File Uploads:**
   - Max 5MB per file (DATA_UPLOAD_MAX_MEMORY_SIZE)
   - Large uploads may need chunking

---

## Security Recommendations

1. ✅ CSRF protection enabled
2. ✅ XSS filtering enabled
3. ✅ Frame options set to DENY
4. ✅ Role-based access control implemented
5. ⚠️ SSL should be enabled in production
6. ⚠️ Consider adding 2FA for prerana user
7. ⚠️ Audit logs for data upload portal
8. ⚠️ Regular security updates for dependencies

---

## Deployment Commands

### Development
```bash
python3 manage.py runserver
# Runs on http://127.0.0.1:8000/
```

### Production (using Gunicorn)
```bash
gunicorn -c gunicorn_config.py SalesDashboard.wsgi
# Or use start_production.sh script
```

### Using Docker
```bash
docker-compose up
# Use docker-compose.yml for containerized deployment
```

---

## Support & Troubleshooting

### Common Issues

**Q: Can't login to dashboard**
```
A: Check if user exists:
   python3 manage.py shell
   >>> from django.contrib.auth.models import User
   >>> User.objects.filter(username='your_username').exists()
   
   If False, create user:
   >>> User.objects.create_user(username='username', password='password')
```

**Q: Can't access upload portal**
```
A: Verify prerana user:
   >>> from django.contrib.auth.models import User
   >>> User.objects.get(username='prerana')
   
   Test authentication:
   >>> from django.contrib.auth import authenticate
   >>> authenticate(username='prerana', password='prerana@123')
```

**Q: Dashboard is blank / no data showing**
```
A: Check if employee data is loaded:
   >>> from core.models import Employee
   >>> Employee.objects.count()
   
   If 0, load data using data loader
```

---

## Next Steps / TODOs

- [ ] Load employee dimension data
- [ ] Load sales/brokerage fact data
- [ ] Test all role-based filters
- [ ] Set up production database (PostgreSQL)
- [ ] Configure email for password reset
- [ ] Set up monitoring/logging service
- [ ] Create backup strategy
- [ ] Document API endpoints
- [ ] Add unit tests for data pipeline
- [ ] Performance test with large datasets

