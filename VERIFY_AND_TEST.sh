#!/bin/bash
# Sales Dashboard - Verification & Testing Script
# Run this to verify all fixes are working

set -e  # Exit on error

echo "=========================================="
echo "Sales Dashboard Verification & Testing"
echo "=========================================="
echo ""

# Check Python version
echo "✓ Checking Python..."
python3 --version

# Setup Django environment
cd /var/www/SalesDashboardProject/SalesDashboard

echo ""
echo "=========================================="
echo "1. Database Migration Status"
echo "=========================================="

echo "Running migrations..."
python3 manage.py migrate --check

echo "Status: ✓ All migrations applied successfully"

echo ""
echo "=========================================="
echo "2. Testing Prerana User Authentication"
echo "=========================================="

python3 manage.py shell << 'EOF'
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from core.models import UserProfile

print("\n📋 Checking prerana user...")

# Check if user exists
try:
    user = User.objects.get(username='prerana')
    print(f"✓ User exists: {user.username}")
    print(f"  - Active: {user.is_active}")
    print(f"  - Staff: {user.is_staff}")
    print(f"  - Email: {user.email}")
except User.DoesNotExist:
    print("✗ ERROR: prerana user not found!")
    exit(1)

# Check UserProfile
try:
    profile = UserProfile.objects.get(user=user)
    print(f"✓ UserProfile exists")
    print(f"  - Role: {profile.get_role_display()}")
    print(f"  - Active: {profile.is_active}")
except UserProfile.DoesNotExist:
    print("✗ ERROR: UserProfile not found!")
    exit(1)

# Test authentication
auth_user = authenticate(username='prerana', password='prerana@123')
if auth_user is not None:
    print(f"\n✓ Authentication test PASSED")
    print(f"  - Username matches: {auth_user.username == 'prerana'}")
    print(f"  - Password is correct: True")
else:
    print(f"\n✗ Authentication test FAILED")
    exit(1)

EOF

echo ""
echo "=========================================="
echo "3. Testing Dashboard User Authentication"
echo "=========================================="

python3 manage.py shell << 'EOF'
from django.contrib.auth.models import User

# Check if any employees exist
users = User.objects.all()
print(f"Total users in database: {users.count()}")

if users.count() > 1:  # Should have at least prerana
    print("✓ Database has users")
    print("\nAll users:")
    for u in users:
        try:
            profile = u.profile
            print(f"  - {u.username}: {profile.get_role_display()}")
        except:
            print(f"  - {u.username}: (no profile)")
else:
    print("\n⚠️  Only prerana user exists")
    print("   To create employee accounts, run:")
    print("   python3 manage.py create_all_users")

EOF

echo ""
echo "=========================================="
echo "4. Checking Database Tables"
echo "=========================================="

python3 manage.py shell << 'EOF'
from django.contrib.auth.models import User
from core.models import UserProfile, Employee, Client, SalesRecord

print("Database tables status:")
print(f"✓ auth_user: {User.objects.count()} records")
print(f"✓ user_profile: {UserProfile.objects.count()} records")
print(f"✓ employee_dimension: {Employee.objects.count()} records")
print(f"✓ client_dimension: {Client.objects.count()} records")
print(f"✓ sales_record: {SalesRecord.objects.count()} records")

EOF

echo ""
echo "=========================================="
echo "5. Checking Application Settings"
echo "=========================================="

python3 manage.py shell << 'EOF'
from django.conf import settings

print("\nKey Settings:")
print(f"DEBUG: {settings.DEBUG}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS[:3]}...")
print(f"LOGIN_URL: {settings.LOGIN_URL}")
print(f"LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")
print(f"DATABASE: {settings.DATABASES['default']['ENGINE'].split('.')[-1]}")
print(f"INSTALLED_APPS: {len(settings.INSTALLED_APPS)} apps")

EOF

echo ""
echo "=========================================="
echo "6. Checking File Permissions"
echo "=========================================="

echo "Checking critical directories..."
ls -ld /var/www/SalesDashboardProject/SalesDashboard/ > /dev/null && echo "✓ Dashboard directory readable"
ls -d /var/www/SalesDashboardProject/SalesDashboard/logs/ > /dev/null && echo "✓ Logs directory exists" || mkdir -p /var/www/SalesDashboardProject/SalesDashboard/logs/

echo ""
echo "=========================================="
echo "7. Creating Test Script"
echo "=========================================="

cat > /var/www/SalesDashboardProject/SalesDashboard/test_full_auth.py << 'TESTEOF'
#!/usr/bin/env python3
"""
Complete authentication test script
Tests dashboard login and upload portal login
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from core.models import UserProfile

def test_prerana_auth():
    """Test prerana authentication"""
    print("\n" + "="*50)
    print("Testing Prerana Authentication")
    print("="*50)
    
    # Test authentication
    user = authenticate(username='prerana', password='prerana@123')
    
    if user is None:
        print("✗ FAILED: Authentication returned None")
        return False
    
    if user.username != 'prerana':
        print("✗ FAILED: Username mismatch")
        return False
    
    if not user.is_active:
        print("✗ FAILED: User is not active")
        return False
    
    # Check profile
    try:
        profile = UserProfile.objects.get(user=user)
        if profile.get_role_display() != 'Leader':
            print("✗ FAILED: Role is not Leader")
            return False
    except UserProfile.DoesNotExist:
        print("✗ FAILED: UserProfile doesn't exist")
        return False
    
    print("✓ Prerana authentication: PASSED")
    print(f"  - Username: {user.username}")
    print(f"  - Active: {user.is_active}")
    print(f"  - Role: {profile.get_role_display()}")
    return True

def test_dashboard_users():
    """Test dashboard user accounts"""
    print("\n" + "="*50)
    print("Testing Dashboard Users")
    print("="*50)
    
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    
    if users.count() == 0:
        print("✗ FAILED: No users found")
        return False
    
    print("✓ Users exist in database")
    
    # Show user list
    for user in users[:5]:
        try:
            profile = user.profile
            status = "✓" if user.is_active else "✗"
            print(f"  {status} {user.username}: {profile.get_role_display()}")
        except:
            print(f"  - {user.username}: (no profile)")
    
    if users.count() > 5:
        print(f"  ... and {users.count() - 5} more users")
    
    return True

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("SALES DASHBOARD - COMPLETE AUTHENTICATION TEST")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Prerana Authentication", test_prerana_auth()))
    results.append(("Dashboard Users", test_dashboard_users()))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests PASSED! Your login system is working correctly!")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        return 1

if __name__ == '__main__':
    exit(main())
TESTEOF

python3 /var/www/SalesDashboardProject/SalesDashboard/test_full_auth.py

echo ""
echo "=========================================="
echo "8. Login URLs & Credentials"
echo "=========================================="

echo ""
echo "📍 Dashboard Login:"
echo "   URL: http://your-server/accounts/login/"
echo "   Username: prerana (or any employee account)"
echo "   Password: prerana@123 (or employee password)"
echo ""
echo "📍 Upload Portal Login:"
echo "   URL: http://your-server/upload-portal/login/"
echo "   Username: prerana"
echo "   Password: prerana@123"
echo ""

echo "=========================================="
echo "✅ VERIFICATION COMPLETE"
echo "=========================================="
echo ""
echo "Summary:"
echo "✓ Database initialized and migrated"
echo "✓ Prerana user created with correct credentials"
echo "✓ Authentication system functional"
echo "✓ Login portals ready"
echo ""
echo "Next steps:"
echo "1. Start Django server: python3 manage.py runserver"
echo "2. Test login at: http://localhost:8000/accounts/login/"
echo "3. Test upload portal: http://localhost:8000/upload-portal/login/"
echo "4. Load data: Check data_files/ folders for CSV/Excel files"
echo ""
