#!/usr/bin/env python3
"""
Test upload portal login on production server.
This script directly connects to the production server and tests the login flow.
"""
import requests
import re
import sys
from urllib.parse import urljoin

# Configuration
LIVE_SERVER = "https://1capital.in"
LOGIN_URL = urljoin(LIVE_SERVER, "/upload-portal/login/")
PORTAL_URL = urljoin(LIVE_SERVER, "/upload-portal/")
CREDENTIALS = {
    'username': 'prerana',
    'password': 'prerana@123'
}

print("=" * 80)
print("UPLOAD PORTAL LOGIN - PRODUCTION SERVER TEST")
print("=" * 80)

# Create session to maintain cookies
session = requests.Session()
session.verify = True  # Verify SSL certificate

print(f"\n[TEST 1] Connecting to login page...")
print(f"   URL: {LOGIN_URL}")

try:
    response = session.get(LOGIN_URL)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Login page accessible")
        
        # Extract CSRF token (handle both single and double quotes)
        match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', response.text)
        if match:
            csrf_token = match.group(1)
            print(f"   ✅ CSRF token found: {csrf_token[:30]}...")
        else:
            print("   ⚠️  CSRF token not found in page")
            csrf_token = None
        
        print(f"\n[TEST 2] Submitting login credentials...")
        print(f"   Username: {CREDENTIALS['username']}")
        print(f"   Password: {'*' * len(CREDENTIALS['password'])}")
        
        # Prepare login data
        login_data = {
            'username': CREDENTIALS['username'],
            'password': CREDENTIALS['password'],
        }
        if csrf_token:
            login_data['csrfmiddlewaretoken'] = csrf_token
        
        # Submit login form with Referer header for CSRF validation
        headers = {
            'Referer': LOGIN_URL
        }
        response = session.post(LOGIN_URL, data=login_data, allow_redirects=False, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 302:
            # Got a redirect - check where it goes
            redirect_location = response.headers.get('Location', 'unknown')
            print(f"   ✅ Redirected to: {redirect_location}")
            
            # Check if it's going to the portal
            if 'upload-portal/' in redirect_location:
                print("   ✅ Redirecting to upload portal (correct!)")
            
            print(f"\n[TEST 3] Following redirect to access portal...")
            response = session.get(urljoin(LIVE_SERVER, redirect_location), allow_redirects=False)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Successfully authenticated and accessed upload portal!")
                
                # Check for portal content
                if 'brokerage' in response.text.lower() or 'upload' in response.text.lower():
                    print("   ✅ Portal content found!")
                    print("\n" + "=" * 80)
                    print("✅ LOGIN TEST PASSED - Upload portal is working!")
                    print("=" * 80)
                    sys.exit(0)
                else:
                    print("   ⚠️  Portal content not fully verified")
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                if response.status_code == 302:
                    print(f"   Redirecting to: {response.headers.get('Location', 'unknown')}")
        
        elif response.status_code == 200:
            print("   ❌ Form submission returned 200 (should redirect)")
            # Check for error message
            if 'Invalid credentials' in response.text:
                print("   ❌ Invalid credentials error!")
            elif 'authorized' in response.text.lower():
                print("   ❌ Authorization error!")
            else:
                print("   ❌ No error message, but no redirect")
        
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
    
    elif response.status_code == 301:
        print(f"   ⚠️  Got 301 redirect to: {response.headers.get('Location', 'unknown')}")
        print("   ❌ SSL redirect issue might not be fixed!")
        sys.exit(1)
    
    elif response.status_code == 404:
        print("   ❌ Login page not found (404)")
        sys.exit(1)
    
    else:
        print(f"   ❌ Unexpected status: {response.status_code}")
        sys.exit(1)

except requests.exceptions.SSLError as e:
    print(f"   ❌ SSL Error: {e}")
    print("   (This might be expected for self-signed certificates in test environments)")
    sys.exit(1)

except requests.exceptions.ConnectionError as e:
    print(f"   ❌ Connection Error: {e}")
    sys.exit(1)

except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("❌ LOGIN TEST FAILED OR INCOMPLETE")
print("=" * 80)
sys.exit(1)
