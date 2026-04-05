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
print("LOGIN TEST - HTTPS CLIENT")
print("=" * 80)

# Use HTTPS in test client
client = Client(secure=True)

# Step 1: Verify user exists
print("\n[STEP 1] Verifying user...")
try:
    user = User.objects.get(username='prerana')
    print(f"✅ User 'prerana' exists (Active: {user.is_active})")
except User.DoesNotExist:
    print("❌ User not found")
    sys.exit(1)

# Step 2: Get login page (HTTPS)
print("\n[STEP 2] Getting login page via HTTPS...")
response = client.get('/upload-portal/login/')
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    print("   ✅ Login page loaded")
    # Extract CSRF token
    import re
    match = re.search(b"name='csrfmiddlewaretoken' value='([^']+)'", response.content)
    if match:
        csrf_token = match.group(1).decode('utf-8')
        print(f"   ✅ CSRF token found: {csrf_token[:20]}...")
    else:
        print("   ⚠️  CSRF token not found...")
        csrf_token = None
elif response.status_code == 301:
    print(f"   ⚠️  Got 301 redirect to: {response.get('Location', 'unknown')}")
    csrf_token = None
else:
    print(f"   ❌ Unexpected response code: {response.status_code}")
    csrf_token = None

# Step 3: Submit login form
print("\n[STEP 3] Submitting login form...")
data = {
    'username': 'prerana',
    'password': 'prerana@123',
}
if csrf_token:
    data['csrfmiddlewaretoken'] = csrf_token

response = client.post('/upload-portal/login/', data, follow=False)
print(f"   Status: {response.status_code}")

if response.status_code == 302:
    print(f"   ✅ Redirecting to: {response.get('Location', 'unknown')}")
    csrf_token_worked = True
elif response.status_code == 200:
    print("   ✅ Form submitted, checking if authenticated...")
    csrf_token_worked = False
else:
    print(f"   ❌ Unexpected status: {response.status_code}")
    csrf_token_worked = False

# Step 4: Check session
print("\n[STEP 4] Checking session...")
if 'sessionid' in client.cookies:
    print(f"   ✅ sessionid cookie: {client.cookies['sessionid'].value[:30]}...")
    has_session = True
else:
    print("   ❌ No sessionid cookie")
    has_session = False

# Step 5: Try to access portal
print("\n[STEP 5] Accessing upload portal...")
response = client.get('/upload-portal/', follow=False)
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    print("   ✅ Authenticated! Can access portal")
    # Check if page has upload elements
    if b'brokerage' in response.content:
        print("   ✅ Portal content found (file upload elements present)")
    else:
        print("   ⚠️  Portal might not have full content")
elif response.status_code == 302:
    location = response.get('Location', 'unknown')
    print(f"   ❌ Redirecting to: {location}")
    if 'login' in location:
        print("   ❌ Not authenticated - redirecting to login")
    else:
        print(f"   ⚠️  Unexpected redirect")
else:
    print(f"   ❌ Unexpected status: {response.status_code}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
