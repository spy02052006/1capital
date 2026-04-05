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
print("LOAD SALES DATA - FIXED VERSION")
print("="*120)

def safe_decimal(val):
    try:
        if pd.isna(val) or val == '':
            return Decimal('0')
        return Decimal(str(val))
    except:
        return Decimal('0')

# Step 1: Load Brokerage data
print(f"\n[1/2] Loading Brokerage Data...")
print("-"*120)

brk_dir = DATA_ROOT / 'brokerage_fact'
sales_count = 0
skipped = 0

for file_path in brk_dir.glob('*.xlsx'):
    print(f"  Reading: {file_path.name}")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        
        for idx, row in df.iterrows():
            try:
                client_code = str(row.get('Client Code', '')).strip()
                wire_code = str(row.get('WireCode', '')).strip()
                
                if not client_code or not wire_code:
                    skipped += 1
                    continue
                
                # Find employee by wire code
                emp = Employee.objects.filter(wire_code__iexact=wire_code).first()
                if not emp:
                    skipped += 1
                    continue
                
                # Find or create client
                client, created = Client.objects.get_or_create(
                    client_code=client_code,
                    defaults={
                        'client_name': str(row.get('Client Name', client_code)).strip() or client_code,
                        'employee': emp,
                        'rm_name': emp.rm_name,
                    }
                )
                
                # Get financial data
                total_brk = safe_decimal(row.get('Total Brokerage', 0))
                
                # Skip if zero
                if total_brk == 0:
                    skipped += 1
                    continue
                
                cash_delivery = safe_decimal(row.get('Cash Delivery', 0))
                cash_intraday = safe_decimal(row.get('Cash Intraday', 0))
                equ_cash_delivery_turnover = safe_decimal(row.get('Equity Cash Delivery Turnover', 0))
                equ_cash_intraday_turnover = safe_decimal(row.get('Equity Cash Intraday Turnover', 0))
                futures_turnover = safe_decimal(row.get('Equity Futures Turnover', 0))
                options_turnover = safe_decimal(row.get('Equity Options Turnover', 0))
                
                # Create sales record
                SalesRecord.objects.create(
                    employee=emp,
                    client=client,
                    rm_name=emp.rm_name,
                    client_name=client.client_name,
                    client_code=client_code,
                    wire_code=wire_code,
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
                skipped += 1
                
    except Exception as e:
        print(f"    Error: {e}")

print(f"[OK] Brokerage Records Loaded: {sales_count}")
print(f"    Skipped (no data or not found): {skipped}")

# Step 2: Load MF data
print(f"\n[2/2] Loading MF Data...")
print("-"*120)

mf_dir = DATA_ROOT / 'MF_fact'
mf_count = 0
mf_skipped = 0

for file_path in mf_dir.glob('*.xlsx'):
    print(f"  Reading: {file_path.name}")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        
        for idx, row in df.iterrows():
            try:
                brokerage = safe_decimal(row.get('BROKERAGE', 0))
                
                if brokerage == 0:
                    mf_skipped += 1
                    continue
                
                investor_name = str(row.get('INV_NAME', 'MF Investor')).strip() or 'MF Investor'
                
                # Create MF record without employee link
                SalesRecord.objects.create(
                    client_name=investor_name,
                    mf_brokerage=brokerage,
                    source_file=file_path.name,
                )
                mf_count += 1
                
            except Exception as e:
                mf_skipped += 1
    except Exception as e:
        print(f"    Error: {e}")

print(f"[OK] MF Records Loaded: {mf_count}")
print(f"    Skipped (no brokerage): {mf_skipped}")

# Verify
print(f"\n" + "="*120)
print(f"VERIFICATION")
print(f"="*120)

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
top_rms = list(SalesRecord.objects.values('rm_name').annotate(
    total=Sum('total_brokerage'),
    mf_total=Sum('mf_brokerage'),
    record_count=Count('id')
).filter(rm_name__isnull=False).order_by('-total')[:10])

for rm in top_rms:
    print(f"  {rm['rm_name']:30} | Records: {rm['record_count']:5} | Brokerage: ₹{rm['total'] or 0:>14,.2f} | MF: ₹{rm['mf_total'] or 0:>14,.2f}")

print(f"\n" + "="*120)
print(f"DATA LOAD COMPLETE!")
print(f"="*120)
