#!/usr/bin/env python3
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from core.models import UserProfile

print("=" * 80)
print("LOGIN DEBUGGING - FORM SUBMISSION TEST")
print("=" * 80)

# Step 1: Verify user exists
print("\n[STEP 1] Creating TEST client and checking user...")
client = Client()
try:
    user = User.objects.get(username='prerana')
    print(f"✅ User 'prerana' exists")
    print(f"   - Password algorithm: {user.password.split('$')[0]}")
    print(f"   - Active: {user.is_active}")
except User.DoesNotExist:
    print("❌ User 'prerana' does not exist")
    sys.exit(1)

# Step 2: Test direct authentication
print("\n[STEP 2] Testing direct authentication (outside of test client)...")
auth_user = authenticate(username='prerana', password='prerana@123')
if auth_user:
    print(f"✅ authenticate() returned user object: {auth_user}")
else:
    print("❌ authenticate() returned None")
    sys.exit(1)

# Step 3: Test form submission via test client
print("\n[STEP 3] Testing form submission via test client...")

# First, get the login page to see response
response = client.get('/upload-portal/login/')
print(f"   GET /upload-portal/login/: Status {response.status_code}")

# Check if CSRF token is in response
if b'csrfmiddlewaretoken' in response.content:
    print("   ✅ CSRF token present in login page")
    # Extract CSRF token
    import re
    match = re.search(b"name='csrfmiddlewaretoken' value='([^']+)'", response.content)
    if match:
        csrf_token = match.group(1).decode('utf-8')
        print(f"   ✅ CSRF token extracted: {csrf_token[:20]}...")
    else:
        print("   ⚠️  Could not extract CSRF token from regex")
        csrf_token = None
else:
    print("   ❌ CSRF token NOT found in login page")
    csrf_token = None

# Now submit the login form
print("\n[STEP 4] Submitting login form with credentials...")
data = {
    'username': 'prerana',
    'password': 'prerana@123',
}
if csrf_token:
    data['csrfmiddlewaretoken'] = csrf_token

response = client.post('/upload-portal/login/', data, follow=True)
print(f"   POST /upload-portal/login/: Status {response.status_code}")
print(f"   Redirect chain: {response.redirect_chain}")

# Step 5: Check if authenticated
print("\n[STEP 5] Checking session/authentication state...")
if response.wsgi_request:
    print(f"   is_authenticated: {response.wsgi_request.user.is_authenticated}")
    if response.wsgi_request.user.is_authenticated:
        print(f"   username: {response.wsgi_request.user.username}")
    else:
        print("   ❌ User is NOT authenticated after login")

# Step 6: Check cookies
print("\n[STEP 6] Checking session cookies...")
if 'sessionid' in client.cookies:
    print(f"   ✅ sessionid cookie present: {client.cookies['sessionid'].value[:20]}...")
else:
    print("   ❌ sessionid cookie NOT present")

# Step 7: Get upload portal page
print("\n[STEP 7] Attempting to access upload portal...")
response = client.get('/upload-portal/', follow=True)
print(f"   GET /upload-portal/: Status {response.status_code}")
print(f"   Redirect chain: {response.redirect_chain}")
print(f"   Final URL requested: {response.wsgi_request.path}")

# Check for error message in response
if b'Invalid credentials' in response.content:
    print("   ❌ 'Invalid credentials' error found in response")
elif b'Only authorized' in response.content:
    print("   ❌ 'Only authorized' error found in response")
else:
    print("   ✅ No error message found")

print("\n" + "=" * 80)
print("DEBUGGING COMPLETE")
print("=" * 80)
print("\nTo debug further, check:")
print("1. Django logs: tail -f logs/dashboard.log")
print("2. authenticate() return value and user checks")
print("3. Session cookie creation and validation")
print("4. CSRF token generation and validation")
