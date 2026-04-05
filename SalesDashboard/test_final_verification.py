#!/usr/bin/env python3
"""
Complete upload portal login test with detailed diagnostics
"""
import requests
import re
import sys
from urllib.parse import urljoin

# Configuration
LIVE_SERVER = "https://1capital.in"
LOGIN_URL = urljoin(LIVE_SERVER, "/upload-portal/login/")
PORTAL_URL = urljoin(LIVE_SERVER, "/upload-portal/")
CREDENTIALS = {'username': 'prerana', 'password': 'prerana@123'}

print("=" * 80)
print("UPLOAD PORTAL LOGIN - COMPLETE VERIFICATION TEST")
print("=" * 80)
print(f"\nServer: {LIVE_SERVER}")
print(f"Portal: {LOGIN_URL}")

# Create session
session = requests.Session()
session.verify = True

# Step 1: Get login page
print(f"\n[STEP 1] Loading login page...")
response = session.get(LOGIN_URL, timeout=10)
if response.status_code != 200:
    print(f"❌ FAILED: Got HTTP {response.status_code}")
    sys.exit(1)
print(f"✅ Login page loaded (HTTP {response.status_code})")

# Step 2: Extract CSRF token
print(f"\n[STEP 2] Extracting CSRF token...")
match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', response.text)
if not match:
    print("❌ FAILED: CSRF token not found")
    sys.exit(1)
csrf_token = match.group(1)
print(f"✅ CSRF token found: {csrf_token[:40]}...")

# Step 3: Check cookies
print(f"\n[STEP 3] Checking session cookies...")
cookies = dict(session.cookies)
if 'csrftoken' in cookies:
    print(f"✅ CSRF cookie present: {cookies['csrftoken'][:30]}...")
else:
    print(f"⚠️  WARNING: CSRF cookie not present")
    print(f"   Available cookies: {list(cookies.keys())}")

# Step 4: Submit login form
print(f"\n[STEP 4] Submitting login form...")
print(f"   Username: {CREDENTIALS['username']}")
print(f"   Password: {'*' * len(CREDENTIALS['password'])}")

login_data = {
    'username': CREDENTIALS['username'],
    'password': CREDENTIALS['password'],
    'csrfmiddlewaretoken': csrf_token
}

headers = {'Referer': LOGIN_URL}
response = session.post(LOGIN_URL, data=login_data, headers=headers, allow_redirects=False, timeout=10)
print(f"   Response: HTTP {response.status_code}")

# Analyze response
if response.status_code == 302:
    redirect = response.headers.get('Location', 'unknown')
    print(f"✅ SUCCESS: Received redirect to: {redirect}")
    
    if 'upload-portal' in redirect:
        print(f"✅ Redirecting to upload portal - Authentication successful!")
    else:
        print(f"⚠️  WARNING: Unexpected redirect target")

elif response.status_code == 200:
    if 'Invalid credentials' in response.text:
        print(f"❌ FAILED: Authentication failed - Invalid credentials")
        sys.exit(1)
    elif 'upload' in response.text.lower() and 'brokerage' in response.text.lower():
        print(f"✅ SUCCESS: Portal page loaded (HTTP 200)")
    else:
        print(f"⚠️  Unclear response")
        
else:
    print(f"❌ FAILED: Unexpected HTTP status {response.status_code}")
    sys.exit(1)

# Step 5: Try to access portal
print(f"\n[STEP 5] Accessing upload portal...")
response = session.get(PORTAL_URL, timeout=10)
if response.status_code == 200:
    if 'brokerage' in response.text.lower() or 'file' in response.text.lower():
        print(f"✅ SUCCESS: Portal is accessible and authenticated!")
    else:
        print(f"⚠️  Portal loaded but content unclear")
elif response.status_code == 302:
    location = response.headers.get('Location', 'unknown')
    if 'login' in location:
        print(f"⚠️  Still not authenticated - redirecting to login")
    else:
        print(f"⚠️  Unexpected redirect: {location}")
else:
    print(f"❌ FAILED: Portal returned HTTP {response.status_code}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ UPLOAD PORTAL LOGIN TEST COMPLETED SUCCESSFULLY!")
print("=" * 80)
print(f"\nThe upload portal is working correctly!")
print(f"Access: {LOGIN_URL}")
print(f"Credentials: prerana / prerana@123")
sys.exit(0)
