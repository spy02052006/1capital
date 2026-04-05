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

from core.models import Employee, Client, SalesRecord, UserProfile
from django.contrib.auth.models import User

print("="*100)
print("LOAD CLIENTS AND SALES DATA (KEEP EMPLOYEES)")
print("="*100)

# Step 1: Load all clients
print(f"\n[1/4] Loading Clients...")
print("-"*100)

client_dir = DATA_ROOT / 'Client_dim'
client_count = 0

for file_path in client_dir.glob('*.xlsx'):
    print(f"  Reading: {file_path.name}")
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    
    for idx, row in df.iterrows():
        try:
            client_code = str(row.get('client code', '')).strip()
            client_name = str(row.get('client name', '')).strip()
            rm_name = str(row.get('RM', '')).strip()
            
            if not client_code or not client_name:
                continue
            
            # Find employee by rm_name
            emp = Employee.objects.filter(rm_name__iexact=rm_name).first()
            
            client, created = Client.objects.get_or_create(
                client_code=client_code,
                defaults={
                    'client_name': client_name,
                    'employee': emp,
                    'rm_name': rm_name,
                }
            )
            if created:
                client_count += 1
        except Exception as e:
            pass

print(f"[OK] Clients Loaded: {client_count}")

# Step 2: Load brokerage data
print(f"\n[2/4] Loading Brokerage Fact Data...")
print("-"*100)

brk_dir = DATA_ROOT / 'brokerage_fact'
brk_count = 0

for file_path in brk_dir.glob('*.xlsx'):
    print(f"  Processing: {file_path.name}")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        
        for idx, row in df.iterrows():
            try:
                rm_name = str(row.get('RM', '')).strip()
                client_code = str(row.get('Client Code', '')).strip()
                client_name = str(row.get('Client Name', '')).strip()
                
                if not rm_name or not client_code:
                    continue
                
                # Find employee and client
                emp = Employee.objects.filter(rm_name__iexact=rm_name).first()
                client = Client.objects.filter(client_code=client_code).first()
                
                # Extract financial metrics
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
                equity_cash_delivery_turnover = safe_decimal(row.get('Equity Cash Delivery Turnover', 0))
                equity_cash_intraday_turnover = safe_decimal(row.get('Equity Cash Intraday Turnover', 0))
                equity_cash_delivery_charges = safe_decimal(row.get('Equity Cash Delivery Charges', 0))
                equity_cash_intraday_charges = safe_decimal(row.get('Equity Cash Intraday Charges', 0))
                futures_turnover = safe_decimal(row.get('Futures Turnover', 0))
                futures_charges = safe_decimal(row.get('Futures Charges', 0))
                options_turnover = safe_decimal(row.get('Options Turnover', 0))
                options_charges = safe_decimal(row.get('Options Charges', 0))
                
                sr = SalesRecord.objects.create(
                    employee=emp,
                    client=client,
                    rm_name=rm_name,
                    client_name=client_name,
                    client_code=client_code,
                    total_brokerage=total_brk,
                    cash_delivery=cash_delivery,
                    cash_intraday=cash_intraday,
                    equity_cash_delivery_turnover=equity_cash_delivery_turnover,
                    equity_cash_intraday_turnover=equity_cash_intraday_turnover,
                    equity_cash_delivery_charges=equity_cash_delivery_charges,
                    equity_cash_intraday_charges=equity_cash_intraday_charges,
                    futures_turnover=futures_turnover,
                    futures_charges=futures_charges,
                    options_turnover=options_turnover,
                    options_charges=options_charges,
                    source_file=file_path.name,
                )
                brk_count += 1
            except Exception as e:
                pass
    except Exception as e:
        print(f"    Error reading file: {e}")

print(f"[OK] Brokerage Records Loaded: {brk_count}")

# Step 3: Load MF data
print(f"\n[3/4] Loading MF Fact Data...")
print("-"*100)

mf_dir = DATA_ROOT / 'MF_fact'
mf_count = 0

for file_path in mf_dir.glob('*.xlsx'):
    print(f"  Processing: {file_path.name}")
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        
        for idx, row in df.iterrows():
            try:
                rm_name = str(row.get('RM', '')).strip()
                client_code = str(row.get('Client Code', '')).strip()
                client_name = str(row.get('Client Name', '')).strip()
                
                if not rm_name or not client_code:
                    continue
                
                emp = Employee.objects.filter(rm_name__iexact=rm_name).first()
                client = Client.objects.filter(client_code=client_code).first()
                
                def safe_decimal(val):
                    try:
                        if pd.isna(val) or val == '':
                            return Decimal('0')
                        return Decimal(str(val))
                    except:
                        return Decimal('0')
                
                mf_brokerage = safe_decimal(row.get('MF Brokerage', 0))
                
                # Update or create
                sr, created = SalesRecord.objects.get_or_create(
                    employee=emp,
                    client=client,
                    rm_name=rm_name,
                    defaults={
                        'client_name': client_name,
                        'client_code': client_code,
                        'mf_brokerage': mf_brokerage,
                        'source_file': file_path.name,
                    }
                )
                
                if not created:
                    sr.mf_brokerage = mf_brokerage
                    sr.save()
                
                mf_count += 1
            except Exception as e:
                pass
    except Exception as e:
        print(f"    Error reading file: {e}")

print(f"[OK] MF Records Loaded: {mf_count}")

# Step 4: Verify
print(f"\n[4/4] Verification...")
print("-"*100)

from django.db.models import Sum

total_sales = SalesRecord.objects.count()
total_clients = Client.objects.count()
total_brokerage = SalesRecord.objects.aggregate(Sum('total_brokerage'))['total_brokerage__sum'] or 0
total_mf = SalesRecord.objects.aggregate(Sum('mf_brokerage'))['mf_brokerage__sum'] or 0

print(f"[OK] Total Sales Records: {total_sales}")
print(f"[OK] Total Clients: {total_clients}")
print(f"[OK] Total Brokerage: ₹{total_brokerage:,.2f}")
print(f"[OK] Total MF Brokerage: ₹{total_mf:,.2f}")

print("\n" + "="*100)
print("LOAD COMPLETE!")
print("="*100)
