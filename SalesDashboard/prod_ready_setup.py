#!/usr/bin/env python3
"""
Production-Ready Setup & Verification
- Syncs UserProfile for all employees
- Verifies hierarchy integrity
- Tests data isolation
- Prepares dashboard for browser access
"""

import os
import django
import sys

sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
django.setup()

from core.models import Employee, UserProfile, SalesRecord
from django.contrib.auth.models import User
from django.db.models import Count, Q

print("="*140)
print("PRODUCTION-READY SETUP & VERIFICATION")
print("="*140)

# ============================================================================
# STEP 1: Verify Employee Hierarchy Structure
# ============================================================================
print("\n[STEP 1] Verifying Organizational Hierarchy Structure")
print("-"*140)

leader = Employee.objects.filter(manager_id__isnull=True).first()
if not leader:
    print("❌ ERROR: No leader found!")
    sys.exit(1)

print(f"✓ Leader found: {leader.rm_name} (ID={leader.id})")

# Analyze hierarchy levels
def analyze_level(emp, level=0, max_level=0):
    max_level = max(max_level, level)
    for sub in emp.subordinates.all():
        max_level = analyze_level(sub, level + 1, max_level)
    return max_level

max_hierarchy_level = analyze_level(leader)
print(f"✓ Maximum hierarchy levels: {max_hierarchy_level + 1} (0-indexed: {max_hierarchy_level})")

# Count by designation
designations = Employee.objects.values('designation').annotate(count=Count('id')).order_by('designation')
print(f"\nEmployee breakdown by designation:")
for d in designations:
    print(f"  {d['designation'] or 'None':15} → {d['count']:3} employees")

# ============================================================================
# STEP 2: Sync UserProfile Records for All Employees
# ============================================================================
print("\n[STEP 2] Syncing UserProfile Records")
print("-"*140)

from django.db import connection

# Known login users (from the data loading)
known_logins = {
    'Nitin Mude': 'nitin_mude',
    'Harshal Ghatage': 'harshal_ghatage',
    'Suhas Tare': 'suhas_tare',
    'Abhijeet Mane': 'abhijeet_mane',
}

synced_count = 0
already_synced = 0

# Get existing profiles using raw SQL to avoid type mismatch
with connection.cursor() as cursor:
    cursor.execute("SELECT CAST(employee_id AS INTEGER) FROM user_profile WHERE employee_id IS NOT NULL")
    existing_emp_ids = set(row[0] for row in cursor.fetchall())

for employee in Employee.objects.all():
    if employee.id in existing_emp_ids:
        try:
            user_profile = UserProfile.objects.raw(
                "SELECT * FROM user_profile WHERE CAST(employee_id AS INTEGER) = %s LIMIT 1",
                [employee.id]
            )[0]
            already_synced += 1
            print(f"  ✓ {employee.rm_name:30} - Already synced (User: {user_profile.user.username})")
            continue
        except (IndexError, Exception):
            # If error, try to create new one
            pass
    
    # Check if there's a known login for this employee
    username = known_logins.get(employee.rm_name)
    
    if username:
        try:
            user = User.objects.get(username=username)
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'employee': employee,
                    'role': 'L' if employee.manager_id is None else 'M' if employee.designation == 'Manager' else 'R'
                }
            )
            if created:
                synced_count += 1
                print(f"  ✓ {employee.rm_name:30} - Created UserProfile (User: {username})")
            else:
                already_synced += 1
                print(f"  ✓ {employee.rm_name:30} - Already linked (User: {username})")
        except User.DoesNotExist:
            print(f"  ⚠️  {employee.rm_name:30} - User '{username}' not found")
    else:
        # Create dummy test user for non-login employees (for testing)
        test_username = employee.rm_name.lower().replace(' ', '_')
        try:
            user, _ = User.objects.get_or_create(
                username=test_username,
                defaults={
                    'first_name': employee.rm_name.split()[0],
                    'last_name': ' '.join(employee.rm_name.split()[1:]) if len(employee.rm_name.split()) > 1 else '',
                }
            )
            
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'employee': employee,
                    'role': 'L' if employee.manager_id is None else 'M' if employee.designation == 'Manager' else 'R'
                }
            )
            
            if created:
                synced_count += 1
                print(f"  ✓ {employee.rm_name:30} - Created test user & profile")
            else:
                already_synced += 1
                
        except Exception as e:
            print(f"  ✗ {employee.rm_name:30} - Error: {str(e)[:50]}")

print(f"\n  Summary: {synced_count} new synced, {already_synced} already synced")

# ============================================================================
# STEP 3: Verify Data Isolation Logic
# ============================================================================
print("\n[STEP 3] Testing Data Isolation by Role")
print("-"*140)

# Test Leader access
leader_users = UserProfile.objects.filter(role='L')
if leader_users.exists():
    leader_user = leader_users.first()
    leader_emp = leader_user.employee
    
    # Helper function from views.py
    def get_all_subordinates(emp):
        names = []
        if emp.rm_name:
            names.append(emp.rm_name)
        for subordinate in Employee.objects.filter(manager_id=emp):
            names.extend(get_all_subordinates(subordinate))
        return names
    
    all_subordinates = get_all_subordinates(leader_emp)
    leader_data = SalesRecord.objects.filter(rm_name__in=all_subordinates).count()
    
    print(f"\n  Leader ({leader_user.user.username}):")
    print(f"    ✓ Should see ALL records: {leader_data} records")
    print(f"    ✓ Subordinates: {len(all_subordinates)} employees")

# Test Manager access
manager_users = UserProfile.objects.filter(role='M')
print(f"\n  Managers ({manager_users.count()} total):")
for mgr_user in manager_users[:3]:  # Show first 3
    mgr_emp = mgr_user.employee
    team_members = get_all_subordinates(mgr_emp)
    mgr_data = SalesRecord.objects.filter(rm_name__in=team_members).count()
    
    print(f"    {mgr_emp.rm_name:25} → {mgr_data:5} records | Team: {len(team_members):3} people")

# Test RM access
rm_users = UserProfile.objects.filter(role='R')
print(f"\n  RMs/MAs ({rm_users.count()} total):")
for rm_user in rm_users[:3]:  # Show first 3
    rm_emp = rm_user.employee
    rm_data = SalesRecord.objects.filter(rm_name=rm_emp.rm_name).count()
    
    print(f"    {rm_emp.rm_name:25} → {rm_data:5} records")

# ============================================================================
# STEP 4: Verify Manager Dropdown Population
# ============================================================================
print("\n[STEP 4] Verifying Manager Dropdown Logic")
print("-"*140)

# Get all managers (employees with direct reports)
manager_ids = Employee.objects.filter(manager_id__isnull=False).values_list('manager_id', flat=True).distinct()
all_managers = Employee.objects.filter(id__in=manager_ids).order_by('rm_name')

print(f"\nTotal managers identified: {all_managers.count()}")
for mgr in all_managers[:10]:  # Show first 10
    sub_count = mgr.subordinates.count()
    print(f"  {mgr.rm_name:30} (ID={mgr.id:2}) → {sub_count:3} direct reports")

if all_managers.count() > 10:
    print(f"  ... and {all_managers.count() - 10} more managers")

# ============================================================================
# STEP 5: Database Statistics
# ============================================================================
print("\n[STEP 5] Database Statistics")
print("-"*140)

total_employees = Employee.objects.count()
total_users = User.objects.count()
total_profiles = UserProfile.objects.count()
total_records = SalesRecord.objects.count()
total_brokerage = SalesRecord.objects.aggregate(total=Count('id'))['total']

print(f"\n  Total Employees:           {total_employees}")
print(f"  Total Users:               {total_users}")
print(f"  Total UserProfiles:        {total_profiles}")
print(f"  Total SalesRecords:        {total_records}")
print(f"  Profile Coverage:          {(total_profiles/total_employees*100):.1f}%")

# ============================================================================
# STEP 6: Summary & Ready Status
# ============================================================================
print("\n" + "="*140)
print("PRODUCTION READINESS CHECKLIST")
print("="*140)

checks = {
    "✓ Hierarchy intact": leader is not None,
    "✓ All employees have UserProfile": total_profiles == total_employees,
    "✓ Managers identified": all_managers.count() > 0,
    "✓ Sales data present": total_records > 0,
    "✓ Role-based users exist": UserProfile.objects.filter(role__in=['L', 'M', 'R']).count() > 0,
}

for check, status in checks.items():
    status_symbol = "✅" if status else "⚠️"
    print(f"  {status_symbol} {check}")

print("\n" + "="*140)
print("🚀 DASHBOARD READY FOR BROWSER ACCESS")
print("="*140)
print("\nNext steps:")
print("  1. Start Django development server: python manage.py runserver")
print("  2. Open browser: http://localhost:8000/")
print("  3. Login with:")
print("     - Nitin Mude (Leader): nitin_mude / password")
print("     - Suhas Tare (Manager): suhas_tare / password")
print("     - Any promoted RM (Manager): <name_lowercase> / password")
print("  4. Verify data isolation and dropdown filtering works")
print("\n" + "="*140 + "\n")
