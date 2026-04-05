#!/usr/bin/env python3
"""
Load employee data from Excel file and create login accounts.
This script works with the current database schema where wire_code is the primary key.
"""

import os
import sys
import django
import pandas as pd
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
sys.path.insert(0, '/var/www/SalesDashboardProject/SalesDashboard')
django.setup()

from django.contrib.auth.models import User
from core.models import Employee, UserProfile
from django.db import connection

def load_employees_and_users():
    """Load employee data from Excel and create user accounts"""
    
    excel_path = Path('/var/www/SalesDashboardProject/data_files/Employee_dim/Wirecode_wise_RMdetails.xlsx')
    
    if not excel_path.exists():
        print(f"❌ ERROR: Excel file not found at {excel_path}")
        return False
    
    # Read Excel file
    df = pd.read_excel(excel_path)
    
    print("\n" + "="*100)
    print("LOADING EMPLOYEES FROM EXCEL")
    print("="*100)
    print(f"Total employees in file: {len(df)}")
    print(f"Excel columns: {list(df.columns)}")
    
    # Check database schema
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(employee_dimension);")
        columns = cursor.fetchall()
        db_columns = [col[1] for col in columns]
        print(f"Database columns: {db_columns}")
    
    # Clear existing employees
    print("\n[STEP 1] Clearing existing employee records...")
    Employee.objects.all().delete()
    print("✅ Cleared")
    
    # Create a map for building hierarchy
    employees_by_wire_code = {}
    
    # First pass: Create all Employee records
    print("\n[STEP 2] Creating Employee records...")
    created_count = 0
    
    for idx, row in df.iterrows():
        wire_code = str(row['wire code']).strip() if pd.notna(row['wire code']) else f'C{idx:03d}'
        name = str(row['NAME']).strip()
        
        try:
            employee, created = Employee.objects.get_or_create(
                wire_code=wire_code,
                defaults={
                    'rm_name': name,
                    'designation': 'RM/MA',
                    'is_active': True,
                }
            )
            employees_by_wire_code[wire_code] = employee
            if created:
                created_count += 1
        except Exception as e:
            print(f"  ⚠️  Error creating {name}: {e}")
    
    print(f"✅ Created {created_count} employee records")
    
    # Second pass: Create users and profiles
    print("\n[STEP 3] Creating User accounts and UserProfile records...")
    created_users = 0
    updated_users = 0
    
    for idx, row in df.iterrows():
        wire_code = str(row['wire code']).strip() if pd.notna(row['wire code']) else f'C{idx:03d}'
        name = str(row['NAME']).strip()
        
        try:
            employee = employees_by_wire_code[wire_code]
            username = name.lower().replace(" ", "_").replace("-", "_")
            
            # Create or update User
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@onecapital.com',
                    'first_name': name.split()[0] if name else '',
                    'last_name': ' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                }
            )
            
            # Set password to Demo@123456
            user.set_password('Demo@123456')
            user.save()
            
            # Create or update UserProfile
            try:
                profile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                profile = UserProfile(user=user)
            
            profile.employee = employee
            profile.wire_code = wire_code
            
            # For now, assign all as R (RM/MA) - hierarchy will be set later
            profile.role = 'R'
            profile.save()
            
            if user_created:
                created_users += 1
            else:
                updated_users += 1
            
            print(f"  ✓ {name:30} | {username:25} | Wire: {wire_code:10}")
        except Exception as e:
            print(f"  ✗ Error for {name}: {e}")
    
    print(f"\n✅  Created {created_users} new users | Updated {updated_users} existing users")
    
    # Third pass: Set roles based on hierarchy (if manager data is available)
    print("\n[STEP 4] Assigning roles based on employee data...")
    
    # For now, since we don't have manager relationships in the database yet,
    # let's set roles manually or based on a pattern
    # In a real scenario, we'd need to rebuild the manager hierarchy first
    
    leaders = UserProfile.objects.filter(role='L').count()
    managers = UserProfile.objects.filter(role='M').count()
    rms = UserProfile.objects.filter(role='R').count()
    
    print(f"\nRole Distribution:")
    print(f"  Leaders (L): {leaders}")
    print(f"  Managers (M): {managers}")
    print(f"  RM/MA (R): {rms}")
    print(f"  Total: {leaders + managers + rms}")
    
    print("\n" + "="*100)
    print("EMPLOYEE & USER CREATION COMPLETE")
    print("="*100)
    print(f"Total Employees: {Employee.objects.count()}")
    print(f"Total Users: {User.objects.count()}")
    print(f"Total UserProfiles: {UserProfile.objects.count()}")
    print("Password for all users: Demo@123456")
    print("="*100 + "\n")
    
    return True

if __name__ == '__main__':
    success = load_employees_and_users()
    sys.exit(0 if success else 1)
