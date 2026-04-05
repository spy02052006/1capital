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
from django.db.models import Q

print("="*120)
print("DATA LOADER - LOAD CLIENTS AND SALES DATA")
print("="*120)

# Step 1: Build RM mapping from Client files
print(f"\n[1/3] Building RM Name to Client mapping...")
print("-"*120)

rm_to_clients = {}  # {(rm_name, wire_code): [client_codes]}
client_info = {}    # {client_code: (client_name, rm_name, wire_code)}

client_dir = DATA_ROOT / 'Client_dim'
for file_path in client_dir.glob('*.xlsx'):
    print(f"  Reading: {file_path.name}")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        
        for idx, row in df.iterrows():
            try:
                client_code = str(row.get('Client ID/PAN', '')).strip()
                client_name = str(row.get('Client Name', '')).strip()
                rm_name = str(row.get('RM NAME', '')).strip()
                group_code = str(row.get('Group Code', '')).strip()
                
                if not client_code or not client_name or not rm_name:
                    continue
                
                # Store mapping
                key = (rm_name, group_code)
                if key not in rm_to_clients:
                    rm_to_clients[key] = []
                rm_to_clients[key].append(client_code)
                
                client_info[client_code] = {
                    'name': client_name,
                    'rm_name': rm_name,
                    'wire_code': group_code,
                }
            except:
                pass
    except Exception as e:
        print(f"    Error: {e}")

print(f"[OK] Found {len(rm_to_clients)} RM-WireCode combinations")
print(f"[OK] Found {len(client_info)} unique clients")

# Step 2: Create/verify Clients in DB
print(f"\n[2/3] Creating Clients in database...")
print("-"*120)

client_count = 0
for client_code, info in client_info.items():
    try:
        rm_name = info['rm_name']
        wire_code = info['wire_code']
        
        # Find employee by rm_name or wire_code
        emp = Employee.objects.filter(
            Q(rm_name__iexact=rm_name) | Q(wire_code__iexact=wire_code)
        ).first()
        
        client, created = Client.objects.get_or_create(
            client_code=client_code,
            defaults={
                'client_name': info['name'],
                'employee': emp,
                'rm_name': rm_name,
            }
        )
        if created:
            client_count += 1
    except:
        pass

print(f"[OK] Clients created/verified: {client_count}")

# Step 3: Load Brokerage data
print(f"\n[3/3] Loading Brokerage and MF data...")
print("-"*120)

sales_count = 0
brk_dir = DATA_ROOT / 'brokerage_fact'

for file_path in brk_dir.glob('*.xlsx'):
    print(f"  Processing: {file_path.name}")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        
        for idx, row in df.iterrows():
            try:
                client_code = str(row.get('Client Code', '')).strip()
                wire_code = str(row.get('WireCode', '')).strip()
                
                if not client_code:
                    continue
                
                # Get client info
                if client_code not in client_info:
                    continue
                
                client_data = client_info[client_code]
                rm_name = client_data['rm_name']
                
                # Find employee
                emp = Employee.objects.filter(
                    Q(rm_name__iexact=rm_name) | Q(wire_code__iexact=wire_code)
                ).first()
                
                client = Client.objects.filter(client_code=client_code).first()
                
                def safe_decimal(val):
                    try:
                        if pd.isna(val) or val == '':
                            return Decimal('0')
                        return Decimal(str(val))
                    except:
                        return Decimal('0')
                
                total_brk = safe_decimal(row.get('Total Brokerage', 0))
                cash_delivery = safe_decimal(row.get('Cash Delivery', 0))
                cash_intraday = safe_decimal(row.get('Cash Intraday', 0))
                equ_cash_delivery_turnover = safe_decimal(row.get('Equity Cash Delivery Turnover', 0))
                equ_cash_intraday_turnover = safe_decimal(row.get('Equity Cash Intraday Turnover', 0))
                futures_turnover = safe_decimal(row.get('Equity Futures Turnover', 0))
                options_turnover = safe_decimal(row.get('Equity Options Turnover', 0))
                
                # Only create if there's data
                if total_brk > 0:
                    SalesRecord.objects.create(
                        employee=emp,
                        client=client,
                        rm_name=rm_name,
                        client_name=client_data['name'],
                        client_code=client_code,
                        total_brokerage=total_brk,
                        cash_delivery=cash_delivery,
                        cash_intraday=cash_intraday,
                        equity_cash_delivery_turnover=equ_cash_delivery_turnover,
                        equity_cash_intraday_turnover=equ_cash_intraday_turnover,
                        futures_turnover=futures_turnover,
                        options_turnover=options_turnover,
                        source_file=file_path.name,
                    )
                    sales_count += 1
            except Exception as e:
                pass
    except Exception as e:
        print(f"    Error: {e}")

# Load MF data
print(f"\n  Loading MF data...")
mf_dir = DATA_ROOT / 'MF_fact'
mf_count = 0

for file_path in mf_dir.glob('*.xlsx'):
    print(f"  Processing: {file_path.name}")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        
        for idx, row in df.iterrows():
            try:
                # MF data uses different structure - BROKCODE might map to WireCode
                brok_code = str(row.get('BROKCODE', '')).strip()
                investor_name = str(row.get('INV_NAME', '')).strip()
                brokerage = safe_decimal(row.get('BROKERAGE', 0))
                
                if not brok_code or brokerage == 0:
                    continue
                
                # Try to find employee by wire_code
                emp = Employee.objects.filter(wire_code__iexact=brok_code).first()
                if not emp:
                    continue
                
                # Create minimal sales record for MF
                SalesRecord.objects.create(
                    employee=emp,
                    rm_name=emp.rm_name,
                    client_name=investor_name or 'MF Investor',
                    mf_brokerage=brokerage,
                    source_file=file_path.name,
                )
                mf_count += 1
            except:
                pass
    except Exception as e:
        print(f"    Error: {e}")

print(f"[OK] Brokerage Records Loaded: {sales_count}")
print(f"[OK] MF Records Loaded: {mf_count}")

# Verify
print(f"\n" + "="*120)
print(f"VERIFICATION")
print(f"="*120)

from django.db.models import Sum

total_sales = SalesRecord.objects.count()
total_clients = Client.objects.count()
total_brokerage = SalesRecord.objects.aggregate(Sum('total_brokerage'))['total_brokerage__sum'] or 0
total_mf = SalesRecord.objects.aggregate(Sum('mf_brokerage'))['mf_brokerage__sum'] or 0

print(f"\nTotal Sales Records: {total_sales}")
print(f"Total Clients: {total_clients}")
print(f"Total Brokerage: ₹{total_brokerage:,.2f}")
print(f"Total MF Brokerage: ₹{total_mf:,.2f}")
print(f"Total Combined: ₹{(total_brokerage + total_mf):,.2f}")

# Show top RMs
print(f"\nTop 10 RMs by Brokerage:")
print("-"*120)
from django.db.models import Sum
top_rms = SalesRecord.objects.values('rm_name').annotate(
    total=Sum('total_brokerage'),
    mf_total=Sum('mf_brokerage'),
    record_count=Count('id')
).order_by('-total')[:10]

from django.db.models import Count
top_rms = SalesRecord.objects.values('rm_name').annotate(
    total=Sum('total_brokerage'),
    mf_total=Sum('mf_brokerage'),
    record_count=Count('id')
).order_by('-total')[:10]

for rm in top_rms:
    print(f"  {rm['rm_name']:25} | Records: {rm['record_count']:5} | Brokerage: ₹{rm['total'] or 0:>14,.2f} | MF: ₹{rm['mf_total'] or 0:>14,.2f}")

print(f"\n" + "="*120)
print(f"DATA LOAD COMPLETE!")
print(f"="*120)
