import os
import sys
import django
import pandas as pd
from pathlib import Path
from decimal import Decimal

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_ROOT = PROJECT_ROOT / 'data_files'

sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
django.setup()

from core.models import Employee, Client, SalesRecord
from django.db.models import Q, Sum, Count

print("="*120)
print("DEBUG: Check Wire Code and RM Name Matching")
print("="*120)

# First, show what employees we have
print(f"\n[1/5] Employees in Database:")
print("-"*120)
employees = Employee.objects.all().order_by('rm_name')
print(f"Total: {employees.count()}\n")
for emp in employees[:5]:
    print(f"  ID: {emp.id:3} | Wire Code: {emp.wire_code:15} | RM Name: {emp.rm_name:30}")
print(f"  ... and {employees.count()-5} more\n")

# Show what wire codes appear in brokerage files
print(f"\n[2/5] Wire Codes in Brokerage Files:")
print("-"*120)
brk_dir = DATA_ROOT / 'brokerage_fact'
wire_codes_in_files = {}

for file_path in brk_dir.glob('*.xlsx'):
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    for idx, row in df.iterrows():
        wire_code = str(row.get('WireCode', '')).strip()
        if wire_code not in wire_codes_in_files:
            wire_codes_in_files[wire_code] = 0
        wire_codes_in_files[wire_code] += 1

print(f"Total unique wire codes in files: {len(wire_codes_in_files)}")
for wire_code, count in list(wire_codes_in_files.items())[:10]:
    emp = Employee.objects.filter(wire_code__iexact=wire_code).first()
    found = "✓ FOUND" if emp else "✗ NOT FOUND"
    print(f"  {wire_code:15} | Records: {count:5} | {found:15} {emp.rm_name if emp else '(no match)'}")

# Show what RM names appear in Client files
print(f"\n[3/5] RM Names in Client Files:")
print("-"*120)
client_dir = DATA_ROOT / 'Client_dim'
rm_names_in_files = {}

for file_path in client_dir.glob('*.xlsx'):
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    for idx, row in df.iterrows():
        rm_name = str(row.get('RM NAME', '')).strip()
        if rm_name not in rm_names_in_files:
            rm_names_in_files[rm_name] = 0
        rm_names_in_files[rm_name] += 1

print(f"Total unique RM names in files: {len(rm_names_in_files)}")
for rm_name, count in sorted(rm_names_in_files.items())[:10]:
    emp = Employee.objects.filter(rm_name__iexact=rm_name).first()
    found = "✓ FOUND" if emp else "✗ NOT FOUND"
    print(f"  {rm_name:30} | Count: {count:3} | {found:15} {emp.wire_code if emp else '(no match)'}")

# Check MF file structure
print(f"\n[4/5] Broker Codes in MF Files:")
print("-"*120)
mf_dir = DATA_ROOT / 'MF_fact'
brok_codes_in_files = {}

for file_path in mf_dir.glob('*.xlsx'):
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        for idx, row in df.iterrows():
            brok_code = str(row.get('BROKCODE', '')).strip()
            if brok_code and brok_code != 'nan':
                if brok_code not in brok_codes_in_files:
                    brok_codes_in_files[brok_code] = 0
                brok_codes_in_files[brok_code] += 1
    except:
        pass

print(f"Total unique broker codes in MF files: {len(brok_codes_in_files)}")
for brok_code, count in list(sorted(brok_codes_in_files.items(), key=lambda x: x[1], reverse=True))[:5]:
    emp = Employee.objects.filter(wire_code__iexact=brok_code).first()
    found = "✓ FOUND" if emp else "✗ NOT FOUND"
    print(f"  {brok_code:15} | Records: {count:6} | {found:15} {emp.rm_name if emp else '(no match)'}")

print(f"\n[5/5] Summary:")
print("-"*120)
print(f"Employees in DB: {Employee.objects.count()}")
print(f"Clients in DB: {Client.objects.count()}")
print(f"Sales Records in DB: {SalesRecord.objects.count()}")
print(f"\nWire Code Match Rate: {sum(1 for wc in wire_codes_in_files if Employee.objects.filter(wire_code__iexact=wc).exists())}/{len(wire_codes_in_files)}")
print(f"RM Name Match Rate: {sum(1 for rm in rm_names_in_files if Employee.objects.filter(rm_name__iexact=rm).exists())}/{len(rm_names_in_files)}")
