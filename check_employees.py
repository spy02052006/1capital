import os
import django
import sys

# Add the project directory to sys.path
sys.path.insert(0, '/var/www/SalesDashboardProject/SalesDashboard')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
django.setup()

from core.models import Employee, UserProfile, SalesRecord
from django.db.models import Sum

print("="*120)
print("EMPLOYEE_DIM DATA IN DATABASE")
print("="*120)

employees = Employee.objects.all().order_by('rm_name')
print(f"\nTotal Employees in Database: {employees.count()}\n")

for emp in employees:
    manager_name = emp.get_manager_name if emp.manager_id else "NO MANAGER"
    sub_count = emp.subordinates.count()
    
    # Count sales records for this employee
    sales_count = SalesRecord.objects.filter(rm_name=emp.rm_name).count()
    total_brokerage = SalesRecord.objects.filter(rm_name=emp.rm_name).aggregate(Sum('total_brokerage'))['total_brokerage__sum'] or 0
    
    print(f"ID: {emp.id:3} | Name: {emp.rm_name:25} | Designation: {emp.designation or 'N/A':15} | Manager: {manager_name:25} | Subs: {sub_count} | Sales Records: {sales_count:5} | Total ₹{total_brokerage:>14,.2f}")

print("\n" + "="*120)
print("USER PROFILE MAPPING")
print("="*120)

users = UserProfile.objects.all()
print(f"\nTotal Users: {users.count()}\n")

for up in users:
    username = up.user.username
    role = up.get_role_display()
    employee_name = up.employee.rm_name if up.employee else "NOT LINKED"
    
    # Get data visibility
    if up.role == 'L':
        visibility = "ALL DATA (Leader)"
    elif up.role == 'M':
        visibility = f"Manager of {up.employee.rm_name if up.employee else 'N/A'}"
    else:
        visibility = f"Own data ({up.employee.rm_name if up.employee else 'N/A'})"
    
    print(f"User: {username:20} | Role: {role:10} | Linked Employee: {employee_name:25} | Visibility: {visibility}")
