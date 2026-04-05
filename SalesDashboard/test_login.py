#!/usr/bin/env python3
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# Test authentication
user = authenticate(username='prerana', password='prerana@123')
if user is not None:
    print('✓ Authentication successful!')
    print(f'  Username: {user.username}')
    print(f'  Is active: {user.is_active}')
    print(f'  Is staff: {user.is_staff}')
else:
    print('✗ Authentication failed!')
    # Check if user exists
    try:
        u = User.objects.get(username='prerana')
        print(f'User exists: {u.username}')
        print(f'Is active: {u.is_active}')
    except User.DoesNotExist:
        print('User does not exist')
