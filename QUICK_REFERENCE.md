# 🎯 Sales Dashboard - Quick Reference Card

## 📍 Live Server Details
```
Domain:           https://1capital.in
Server IP:        72.61.141.247
Application Path: /var/www/SalesDashboardProject/SalesDashboard
Database Path:    /var/www/SalesDashboardProject/SalesDashboard/db.sqlite3
Backup Path:      /var/www/SalesDashboardProject/backups/
```

---

## 🔐 Login Credentials (SAVE THIS!)

### Prerana User (Data Upload Portal)
```
Username: prerana
Password: prerana@123
Role:     Leader (full access)
Status:   ✓ Active & Verified
```

### Employee Accounts (Optional)
```
Default password: Demo@123456
Created via:      python3 manage.py create_all_users
Role assigned:    Based on hierarchy (Leader/Manager/RM)
```

---

## 🌐 Access Points

| Service | URL | Status |
|---------|-----|--------|
| Dashboard Login | https://1capital.in/accounts/login/ | ✅ Ready |
| Upload Portal | https://1capital.in/upload-portal/login/ | ✅ Ready |
| Admin Panel | https://1capital.in/admin/ | ✅ Ready |
| API Endpoint | https://1capital.in/api/ | ✅ Ready |

---

## ⚙️ Common Commands

### Start/Stop Application
```bash
# Start Gunicorn (if stopped)
sudo systemctl start gunicorn-dashboard

# Stop application
sudo systemctl stop gunicorn-dashboard

# Restart application (after changes)
sudo systemctl restart gunicorn-dashboard

# Check status
sudo systemctl status gunicorn-dashboard
```

### Database Operations
```bash
# Run migrations
cd /var/www/SalesDashboardProject/SalesDashboard
python3 manage.py migrate

# Create employee accounts
python3 manage.py create_all_users

# Check Django shell
python3 manage.py shell

# Collect static files
python3 manage.py collectstatic --noinput
```

### Monitoring
```bash
# View Gunicorn logs
sudo journalctl -u gunicorn-dashboard -f

# View application logs
tail -f /var/www/SalesDashboardProject/SalesDashboard/logs/dashboard.log

# Check running processes
ps aux | grep gunicorn
ps aux | grep python

# Check disk space
df -h /var/www/SalesDashboardProject
```

### Deployment
```bash
# Full deployment with all fixes
bash /var/www/SalesDashboardProject/deploy_to_production.sh

# Restart and verify
bash /var/www/SalesDashboardProject/restart_live_server.sh

# Run tests
bash /var/www/SalesDashboardProject/VERIFY_AND_TEST.sh
```

---

## 🧪 Quick Test Procedures

### Test 1: Login to Dashboard
1. Go to https://1capital.in/accounts/login/
2. Enter: `prerana` / `prerana@123`
3. Expected: Redirect to dashboard with data (if loaded)

### Test 2: Access Upload Portal
1. Go to https://1capital.in/upload-portal/login/
2. Enter: `prerana` / `prerana@123`
3. Expected: See data folders (brokerage, MF, client, employee)

### Test 3: Verify Authentication
```bash
cd /var/www/SalesDashboardProject/SalesDashboard
python3 test_login.py
# Expected output: ✓ Authentication successful!
```

### Test 4: Full Verification
```bash
bash /var/www/SalesDashboardProject/VERIFY_AND_TEST.sh
# Expected: All tests PASSED
```

---

## 🚨 Troubleshooting Quick Links

| Problem | Solution |
|---------|----------|
| Can't login | Check if prerana user exists: `User.objects.get(username='prerana')` |
| App not responding | Restart: `sudo systemctl restart gunicorn-dashboard` |
| Static files missing | Run: `python3 manage.py collectstatic --noinput` |
| Database error | Check migrations: `python3 manage.py migrate --check` |
| Port conflict | Check if 8000 is in use: `lsof -i :8000` |

See `PROJECT_ANALYSIS.md` for detailed troubleshooting.

---

## 📊 System Information

```
Framework:     Django 6.0.3
Python:        3.12.3
Database:      SQLite (production can use PostgreSQL)
Web Server:    Gunicorn (via systemd)
OS:            Linux
Timezone:      Asia/Kolkata
Language:      Python, HTML, CSS, JavaScript
```

---

## 💾 Backup Information

```
Location:      /var/www/SalesDashboardProject/backups/
Latest:        db.sqlite3.backup_20260404_160140
Created during: deploy_to_production.sh
Restore:       cp backup.sql db.sqlite3 (for SQLite)
```

---

## 📞 Support Resources

| Topic | Document |
|-------|----------|
| Technical Details | LOGIN_FIXES_SUMMARY.md |
| Architecture | PROJECT_ANALYSIS.md |
| Quick Start | QUICK_START_GUIDE.md |
| Deployment | DEPLOYMENT_COMPLETE.md |
| Full Guide | START_HERE.md |

All documents are in `/var/www/SalesDashboardProject/`

---

## ✅ Deployment Checklist

- [x] Database migrated
- [x] Prerana user created
- [x] Authentication tested
- [x] Gunicorn running
- [x] Static files collected
- [x] All tests passing
- [x] Security configured
- [x] Backups created
- [x] Documentation complete

**Status:** ✅ READY FOR PRODUCTION

---

## 🔐 Security Notes

1. **Change Prerana Password periodically**
   ```bash
   python3 manage.py shell
   >>> from django.contrib.auth.models import User
   >>> user = User.objects.get(username='prerana')
   >>> user.set_password('new_secure_password')
   >>> user.save()
   ```

2. **Enable 2FA for Prerana (Recommended)**
   - Implement django-otp or similar

3. **Backup Database Weekly**
   ```bash
   cp db.sqlite3 db.sqlite3.backup_$(date +%s)
   ```

4. **Monitor Logs for Suspicious Activity**
   ```bash
   tail -f /var/log/nginx/access.log | grep upload-portal
   ```

---

## 📈 Performance Tips

1. **Cache Configuration** - Already set to 5 minutes
2. **Database Optimization** - Indexes created on key fields
3. **Static File Serving** - Nginx configured
4. **Gunicorn Workers** - Auto-configured for your CPU
5. **Database Connections** - Pool size set to 600 seconds

For large datasets, consider upgrading to PostgreSQL.

---

## 🎓 Learning Resources

- Django Official Docs: https://docs.djangoproject.com/
- Gunicorn Manual: https://docs.gunicorn.org/
- SQL Queries: https://www.postgresql.org/docs/
- Server Security: https://cheatsheetseries.owasp.org/

---

## 📋 Deployment Date & Time
```
Deployed: April 4, 2026
Time:     16:02:22 UTC
Status:   ✅ Complete & Verified
```

---

**Keep this card handy for quick reference!**

For detailed information, see the full documentation files in the project directory.
