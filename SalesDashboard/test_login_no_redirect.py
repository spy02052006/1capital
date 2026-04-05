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
from django.test import override_settings

print("=" * 80)
print("LOGIN TEST - HTTPS CLIENT WITH OVERRIDE")
print("=" * 80)

# Test with override to disable SECURE_SSL_REDIRECT temporarily
with override_settings(SECURE_SSL_REDIRECT=False):
    client = Client(secure=True)
    
    # Step 1: Get login page
    print("\n[STEP 1] Getting login page (SECURE_SSL_REDIRECT disabled)...")
    response = client.get('/upload-portal/login/')
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Login page loaded!")
        
        # Extract CSRF token
        import re
        match = re.search(b"name='csrfmiddlewaretoken' value='([^']+)'", response.content)
        if match:
            csrf_token = match.group(1).decode('utf-8')
            print(f"   ✅ CSRF token found: {csrf_token[:30]}...")
        else:
            print("   ❌ CSRF token not found!")
            csrf_token = None
        
        # Step 2: Submit login form
        print("\n[STEP 2] Submitting login form...")
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
            
            # Step 3: Follow redirect
            print("\n[STEP 3] Following redirect...")
            response = client.get(response['Location'], follow=False)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Successfully accessed portal!")
                if b'brokerage' in response.content or b'upload' in response.content.lower():
                    print("   ✅ Upload portal content found")
                else:
                    print("   ⚠️  Portal content not fully verified")
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
        
        elif response.status_code == 200:
            print("   ⚠️  Got 200 response - checking if authenticated...")
            # Check if there's an error message
            if b'Invalid credentials' in response.content:
                print("   ❌ Invalid credentials error in response")
            else:
                print("   ✅ No error message - might be authenticated")
        
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
    
    elif response.status_code == 301:
        print(f"   ⚠️  Still getting 301 redirect to: {response.get('Location', 'unknown')}")
        print("   This suggests the issue is not SECURE_SSL_REDIRECT")
    
    else:
        print(f"   ❌ Unexpected status: {response.status_code}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
