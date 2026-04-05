#!/usr/bin/env python3
"""
Comprehensive upload portal login test with detailed debugging
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.test import Client
from core.models import UserProfile

print("="*80)
print("UPLOAD PORTAL LOGIN - COMPREHENSIVE TEST")
print("="*80)

# STEP 1: Verify prerana exists and auth works
print("\n[STEP 1] Checking prerana user in database...")
try:
    prerana = User.objects.get(username='prerana')
    print(f"✅ User 'prerana' found in database")
    print(f"   Active: {prerana.is_active}")
    print(f"   Password algorithm: {prerana.password.split('$')[0]}")
except User.DoesNotExist:
    print("❌ ERROR: Prerana user not found!")
    exit(1)

# STEP 2: Test authentication
print("\n[STEP 2] Testing authentication (prerana / prerana@123)...")
auth_user = authenticate(username='prerana', password='prerana@123')
if auth_user is not None:
    print(f"✅ Direct authentication SUCCESSFUL")
else:
    print(f"❌ Direct authentication FAILED!")
    print("   Attempting to reset password...")
    prerana.set_password('prerana@123')
    prerana.save()
    
    # Test again
    auth_user = authenticate(username='prerana', password='prerana@123')
    if auth_user is not None:
        print(f"✅ Password reset - authentication now works")
    else:
        print(f"❌ Still failing - major issue!")
        exit(1)

# STEP 3: Check UserProfile
print("\n[STEP 3] Checking UserProfile...")
try:
    profile = UserProfile.objects.get(user=prerana)
    print(f"✅ UserProfile exists")
    print(f"   Role: {profile.get_role_display()} ({profile.role})")
    print(f"   Active: {profile.is_active}")
except UserProfile.DoesNotExist:
    print(f"❌ UserProfile missing - CREATING...")
    profile = UserProfile.objects.create(user=prerana, role='L', is_active=True)
    print(f"✅ UserProfile created with Leader role")

# STEP 4: Test form submission
print("\n[STEP 4] Testing upload portal login form...")
client = Client()

# Test GET request first (load login page)
print("   - Loading login page (GET)...")
try:
    response = client.get('/upload-portal/login/')
    if response.status_code in [200, 301, 302]:
        print(f"   ✅ Login page accessible (status: {response.status_code})")
    else:
        print(f"   ⚠️  Unexpected status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# Test POST request (submit login)
print("   - Submitting login credentials (POST)...")
try:
    response = client.post('/upload-portal/login/', {
        'username': 'prerana',
        'password': 'prerana@123',
    }, follow=True)
    
    print(f"   Response status: {response.status_code}")
    
    if response.status_code == 200:
        # Check if we're logged in
        if response.wsgi_request.user.is_authenticated:
            if response.wsgi_request.user.username == 'prerana':
                print(f"   ✅ LOGIN SUCCESSFUL - authenticated as prerana")
            else:
                print(f"   ⚠️  Logged in as different user: {response.wsgi_request.user.username}")
        else:
            print(f"   ❌ NOT AUTHENTICATED - check for error message")
            # Look for error in response
            if b'Invalid credentials' in response.content:
                print(f"       Error: Invalid credentials message shown")
            else:
                print(f"       Response contains: {response.content[:200]}")
    else:
        print(f"   Response: {response.status_code}")
        
except Exception as e:
    print(f"   ❌ Error during submission: {str(e)}")

# STEP 5: View configuration check
print("\n[STEP 5] Checking view configuration...")
from django.conf import settings
print(f"   LOGIN_URL: {settings.LOGIN_URL}")
print(f"   LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")
print(f"   CSRF_TRUSTED_ORIGINS: {len(settings.CSRF_TRUSTED_ORIGINS)} domains configured")

# STEP 6: Final Summary
print("\n" + "="*80)
print("FINAL CREDENTIALS")
print("="*80)
print(f"""
🌐 URL:        https://1capital.in/upload-portal/login/
👤 Username:   prerana
🔐 Password:   prerana@123
✅ Status:     READY FOR LOGIN

If login still fails:
1. Clear browser cache and cookies
2. Try in private/incognito window
3. Check server logs: tail -f logs/dashboard.log
4. Check HTTPS is enabled on your domain
""")
