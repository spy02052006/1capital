import os
import django
import sys

sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
django.setup()

from core.models import Employee, SalesRecord
from django.db.models import Count

print("="*140)
print("CREATE LEVEL 3 MANAGERS: PROMOTE RMs WITH MAs TO MANAGERS")
print("="*140)

# Step 1: Find all unique MAs in the sales data
print("\n[STEP 1] Finding all MAs in the system:")
print("-"*140)

all_mas = SalesRecord.objects.exclude(ma_name__isnull=True).exclude(ma_name__exact='').values_list('ma_name', flat=True).distinct()
print(f"Total unique MAs found: {all_mas.count()}")

# Step 2: Find which RMs have MAs assigned
print("\n[STEP 2] Finding RMs that have MAs assigned:")
print("-"*140)

rms_with_mas = {}
for ma_name in all_mas:
    # Find which RMs have this MA
    records_with_ma = SalesRecord.objects.filter(ma_name=ma_name)
    rm_names = records_with_ma.values_list('rm_name', flat=True).distinct()
    
    for rm_name in rm_names:
        if rm_name not in rms_with_mas:
            rms_with_mas[rm_name] = []
        rms_with_mas[rm_name].append(ma_name)

print(f"\nRMs with MAs assigned ({len(rms_with_mas)} RMs):")
for rm_name in sorted([n for n in rms_with_mas.keys() if n], key=str):
    mas = rms_with_mas[rm_name]
    print(f"  RM: {rm_name:30} → {len(set(mas)):2} unique MAs")

# Step 3: Promote RMs to Level 3 Managers and create MA Employee records
print("\n[STEP 3] Promoting RMs to Level 3 Managers and creating MA records:")
print("-"*140)

promoted_count = 0
ma_created_count = 0
ma_linked_count = 0

for rm_name, ma_names in rms_with_mas.items():
    # Skip None RMs
    if not rm_name:
        continue
    
    # Find the RM employee
    rm_emp = Employee.objects.filter(rm_name=rm_name).first()
    
    if not rm_emp:
        print(f"  ⚠️  RM not found: {rm_name}")
        continue
    
    # Mark this RM as a manager by setting designation
    if rm_emp.designation != 'Manager':
        rm_emp.designation = 'Manager'
        rm_emp.save()
        promoted_count += 1
    
    # Create Employee records for each MA
    for ma_name in set(ma_names):  # Use set to avoid duplicates
        # Check if MA already exists as Employee
        ma_emp = Employee.objects.filter(rm_name=ma_name).first()
        
        if not ma_emp:
            # Create new MA Employee record
            # Generate wire code from ma_name
            wire_code = f"MA_{ma_name.upper()[:20]}".replace(" ", "_")
            
            try:
                ma_emp = Employee.objects.create(
                    wire_code=wire_code,
                    rm_name=ma_name,
                    designation='MA',
                    manager_id=rm_emp,  # MA reports to the RM
                    is_active=True
                )
                ma_created_count += 1
                ma_linked_count += 1
            except Exception as e:
                print(f"    ✗ Failed to create MA {ma_name}: {e}")
        else:
            # MA already exists, just update manager if needed
            if ma_emp.manager_id != rm_emp:
                ma_emp.manager_id = rm_emp
                ma_emp.save()
                ma_linked_count += 1

print(f"  ✓ RMs promoted: {promoted_count}")
print(f"  ✓ MAs created: {ma_created_count}")
print(f"  ✓ MAs linked: {ma_linked_count}")

# Step 4: Display the new hierarchy
print(f"\n[STEP 4] New Organizational Structure:")
print("-"*140)

leader = Employee.objects.filter(manager_id__isnull=True).first()

def print_hierarchy(emp, level=0):
    indent = "  " * level
    designation_icon = {
        'Manager': '📊' if level < 2 else '👨‍💼',
        'MA': '👤',
        'Leader': '👑',
    }
    icon = designation_icon.get(emp.designation, '👥')
    
    print(f"{indent}{icon} {emp.rm_name:30} [{emp.designation or 'RM':10}] (ID={emp.id})")
    
    # Print subordinates
    for sub in emp.subordinates.all().order_by('rm_name'):
        print_hierarchy(sub, level + 1)

print("\n")
if leader:
    print_hierarchy(leader)

# Step 5: Hierarchy statistics
print(f"\n{'='*140}")
print(f"[HIERARCHY STATISTICS]")
print("-"*140)

leaders = Employee.objects.filter(manager_id__isnull=True)
level1_managers = Employee.objects.filter(manager_id__in=leaders)
all_managers = Employee.objects.filter(designation='Manager')
all_mas = Employee.objects.filter(designation='MA')
all_rms = Employee.objects.filter(designation__isnull=True, manager_id__isnull=False)

print(f"\n  Level 0 (Leader):                  {leaders.count()}")
print(f"  Level 1 Managers:                  {level1_managers.filter(manager_id__in=leaders).count()}")
print(f"  Level 2 RMs:                       {Employee.objects.filter(manager_id__in=level1_managers.filter(manager_id__in=leaders)).exclude(designation='Manager').count()}")
print(f"  Level 3 Managers (Promoted RMs):   {promoted_count}")
print(f"  Level 4 MAs:                       {all_mas.count()}")
print(f"  Total Employees:                   {Employee.objects.count()}")

print(f"\n{'='*140}")
print("✅ LEVEL 3 MANAGER SETUP COMPLETE!")
print(f"{'='*140}\n")
