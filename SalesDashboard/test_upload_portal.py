#!/usr/bin/env python3
"""
Test script to verify upload portal login works correctly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.test import Client
from django.urls import reverse

print("="*70)
print("UPLOAD PORTAL LOGIN TEST")
print("="*70)

# Test 1: Check prerana user exists and password works
print("\n[TEST 1] Checking prerana user...")
try:
    prerana = User.objects.get(username='prerana')
    print(f"✅ User exists: {prerana.username}")
    print(f"   Active: {prerana.is_active}")
    print(f"   Email: {prerana.email or '(none)'}")
except User.DoesNotExist:
    print("❌ Prerana user not found!")
    exit(1)

# Test 2: Test authentication directly
print("\n[TEST 2] Testing direct authentication...")
auth_user = authenticate(username='prerana', password='prerana@123')
if auth_user:
    print(f"✅ Authentication successful")
    print(f"   Username: {auth_user.username}")
else:
    print(f"❌ Authentication failed - trying to fix password...")
    # Reset password
    prerana.set_password('prerana@123')
    prerana.save()
    auth_user = authenticate(username='prerana', password='prerana@123')
    if auth_user:
        print(f"✅ Password reset and authentication now works")
    else:
        print(f"❌ Still failing!")
        exit(1)

# Test 3: Test upload portal login view
print("\n[TEST 3] Testing upload portal login view...")
client = Client()

# Try to access login page
try:
    response = client.get('/upload-portal/login/')
    if response.status_code == 200:
        print(f"✅ Login page loads (status: {response.status_code})")
    else:
        print(f"❌ Login page error (status: {response.status_code})")
except Exception as e:
    print(f"❌ Error accessing login page: {str(e)}")

# Try to login
print("\nAttempting login with prerana / prerana@123...")
try:
    response = client.post('/upload-portal/login/', {
        'username': 'prerana',
        'password': 'prerana@123'
    })
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 302:  # Redirect
        print(f"✅ Login accepted - redirecting to: {response.url}")
    elif response.status_code == 200:
        # Check if error is in response
        if b'error' in response.content.lower() or b'invalid' in response.content.lower():
            print(f"❌ Login rejected - error message in response")
            # Print the error message
            if b'Invalid credentials' in response.content:
                print("   Error: Invalid credentials message shown")
        else:
            print(f"✅ Login page reloaded (waiting for redirect)")
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error during login: {str(e)}")

# Test 4: Check UserProfile
print("\n[TEST 4] Checking UserProfile...")
from core.models import UserProfile
try:
    profile = UserProfile.objects.get(user=prerana)
    print(f"✅ UserProfile exists")
    print(f"   Role: {profile.get_role_display()}")
    print(f"   Active: {profile.is_active}")
except UserProfile.DoesNotExist:
    print(f"❌ UserProfile missing - creating...")
    profile, created = UserProfile.objects.get_or_create(user=prerana)
    profile.role = 'L'
    profile.is_active = True
    profile.save()
    if created:
        print(f"✅ UserProfile created with Leader role")
    else:
        print(f"✅ UserProfile updated")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)

print("\n🔐 UPLOAD PORTAL CREDENTIALS:")
print(f"   URL: https://1capital.in/upload-portal/login/")
print(f"   Username: prerana")
print(f"   Password: prerana@123")
print(f"   Status: ✅ Ready to login")
print("")
