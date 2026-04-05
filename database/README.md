# Database Module - Excel Data Loading & PostgreSQL Integration

Real-time auto-loading of Excel files from `data_files/` folder into PostgreSQL tables with validation, deduplication, and comprehensive logging.

## Overview

This module provides:
- **4 PostgreSQL tables** with Django ORM models (BrokerageFact, ClientDim, EmployeeDim, MFact)
- **Real-time file watcher** using `watchdog` library
- **Automatic Excel → Database pipeline** with validation and duplicate detection
- **Schema configuration** via YAML (easy updates without code changes)
- **Row-level deduplication** using SHA256 hashing
- **Comprehensive logging** to files and console

## Architecture

```
data_files/
├── brokerage_fact/          → BrokerageFact table
│   └── *.xlsx files
├── Client_dim/              → ClientDim table
│   └── *.xlsx files
├── Employee_dim/            → EmployeeDim table
│   └── *.xlsx files
└── MF_fact/                 → MFact table
    └── *.xlsx files

database/
├── config/
│   └── schema_config.yaml   (Column mappings, data types, validation rules)
├── models/
│   ├── brokerage.py         (BrokerageFact ORM model)
│   ├── client.py            (ClientDim ORM model)
│   ├── employee.py          (EmployeeDim ORM model)
│   └── mf.py                (MFact ORM model)
├── loaders/
│   ├── excel_loader.py      (Read Excel, parse columns)
│   └── data_loader_service.py  (Orchestrate: load → validate → dedup → insert)
├── watchers/
│   └── folder_watcher.py    (Real-time file monitoring)
├── utils/
│   ├── validator.py         (Schema & type validation)
│   └── duplicate_detector.py  (Row hash deduplication)
├── tests/
│   └── test_loaders.py      (Unit tests)
├── logs/                    (Loading logs)
└── start_watcher.py         (Startup script)
```

## Database Schema

### BrokerageFact (27 columns)
Equity brokerage transactions: cash, futures, options, commodities
- Identifiers: client_code, wire_code, transaction_date
- Segments: cash, futures, options, currency, commodity
- Turnover: equity cash, FFnO, total
- VAS: subscription and reversal charges
- Summary: total_brokerage

### ClientDim (7 columns)
Client master data
- Identifiers: client_id_pan (unique), client_name
- Attributes: group_code, onboarded_date, aum, relationship_manager, rm_pan

### EmployeeDim (6 columns)
Employee/RM master data  
- Identifiers: employee_id (unique), name, pan
- Hierarchy: manager_id (for org structure)
- Codes: wire_code, employee_code

### MFact (27 columns)
Mutual fund transactions: purchases, redemptions, fees
- Identifiers: folio_check, investor_name, pan_no
- Transactions: units, amount, rate
- Fees: trail fees, brokerage, avg_assets
- Classification: fee_type, fee_description
- Scheme: scheme_short_name, reference_no
- Channel: broker_code, sub_broker

## Setup & Configuration

### 1. PostgreSQL Connection Setup

Create or update `.env` file in project root:

```bash
# PostgreSQL Configuration
POSTGRES_DB=sales_dashboard
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost  # Or your server IP
POSTGRES_PORT=5432

# Enable PostgreSQL (instead of SQLite)
USE_POSTGRES=True

# Django settings
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-secret-key
```

### 2. Install PostgreSQL Driver

```bash
pip install psycopg2-binary
```

### 3. Create Database Tables

```bash
# From SalesDashboard folder
python manage.py makemigrations database
python manage.py migrate database
```

This creates 4 tables in PostgreSQL:
- `brokerage_fact`  
- `client_dim`
- `employee_dim`
- `mf_fact`

### 4. Configure Schema (Optional - Already Configured)

The `database/config/schema_config.yaml` file defines:
- Excel column names → Database field names
- Data types (string, integer, decimal, date)
- Max lengths, nullable, defaults
- Validation rules

Example:
```yaml
tables:
  brokerage_fact:
    columns:
      - name: "Client Code"
        db_field: "client_code"
        data_type: "string"
        nullable: false
```

To update schema after changing Excel structure:
1. Edit `schema_config.yaml`
2. Restart the file watcher
3. New files will use updated schema

## Usage

### Option 1: Start Real-Time File Watcher

Monitors `data_files/` folders and auto-loads files as they appear:

```bash
cd /var/www/SalesDashboardProject
python database/start_watcher.py
```

Output:
```
2026-03-10 10:30:45,123 - database.watchers.folder_watcher - INFO - File watcher started for 4 folders
2026-03-10 10:30:45,456 - database.watchers.folder_watcher - INFO - Monitoring for Excel files...
2026-03-10 10:35:22,789 - database.watchers.folder_watcher - INFO - Excel file created: /var/www/SalesDashboardProject/data_files/brokerage_fact/f338y(feb 26 brkg).xlsx
2026-03-10 10:35:23,456 - database.loaders.data_loader_service - INFO - Loading 150 rows into BrokerageFact...
2026-03-10 10:35:24,789 - database.loaders.data_loader_service - INFO - Successfully inserted 150 rows into BrokerageFact
```

Keep this running in the background (use `screen`, `nohup`, or systemd service).

### Option 2: Manual Load via Django Management Command

(Create custom management command `core/management/commands/load_excel_data.py`)

```bash
python manage.py load_excel_data --table brokerage_fact
```

### Option 3: Load Programmatically

```python
from database.loaders.data_loader_service import load_table_from_files
from database.models import BrokerageFact
import yaml

# Load config
with open('database/config/schema_config.yaml') as f:
    config = yaml.safe_load(f)

# Load files from brokerage_fact folder
stats = load_table_from_files(
    config['tables']['brokerage_fact'],
    BrokerageFact,
    'data_files/brokerage_fact'
)

print(stats)
# Output: {'table_name': 'BrokerageFact', 'files_processed': 2, 'total_rows_inserted': 300, ...}
```

## Data Pipeline

For each Excel file:

1. **Read**: Parse Excel file with `openpyxl`/`pandas`
2. **Map**: Map Excel column names → database fields (via schema_config.yaml)
3. **Validate**: Check data types, required fields, max lengths
4. **Deduplicate**: Compute SHA256 hash of all columns, skip if hash already in DB
5. **Insert**: Atomic transaction insert with metadata (source_file, loaded_at, row_hash)
6. **Log**: Record results to `database/logs/` and console

### Duplicate Detection Algorithm

For each row:
1. Compute SHA256 hash of all column values concatenated
2. Store hash in `row_hash` database field
3. On next load, check if hash exists
4. If exists, skip row (duplicate)
5. If new, insert row with hash

This detects exact row duplicates even if loaded from different files.

## Validation Rules

From `schema_config.yaml`:

| Column | Type | Max Length | Nullable | Validation |
|--------|------|-----------|----------|-----------|
| Client Code | string | 50 | No | must not be empty |
| WireCode | string | 50 | No | - |
| Date | date | - | No | valid date format |
| Cash Delivery | decimal | - | Yes | numeric |
| ... | ... | ... | ... | ... |

Invalid rows are:
- Logged with specific errors
- Skipped from insert
- Counted in stats

## Logging

Logs are written to:
- **File**: `database/logs/watcher.log` (file watcher activity)
- **File**: `database/logs/loader.log` (data loading details)
- **Console**: Same info printed to terminal

Example log output:
```
2026-03-10 10:35:23,456 - database.loaders.data_loader_service - INFO - ======================================================================
2026-03-10 10:35:23,456 - database.loaders.data_loader_service - INFO - Starting load of file: f338y(feb 26 brkg).xlsx into BrokerageFact
2026-03-10 10:35:23,456 - database.loaders.data_loader_service - INFO - ======================================================================
2026-03-10 10:35:23,789 - database.loaders.data_loader_service - INFO - Loaded 150 rows from Excel
2026-03-10 10:35:24,123 - database.loaders.data_loader_service - INFO - After deduplication: 145 rows ready for insert
2026-03-10 10:35:24,789 - database.loaders.data_loader_service - INFO - Successfully inserted 145 rows into BrokerageFact
2026-03-10 10:35:24,789 - database.loaders.data_loader_service - INFO - Summary: 145 inserted, 5 duplicates, 0 failed
```

## Monitoring

### Check Loading Status

```bash
# Watch the log file in real-time
tail -f database/logs/watcher.log

# Or use Django shell
python manage.py shell
>>> from database.models import BrokerageFact
>>> BrokerageFact.objects.count()
1245
>>> BrokerageFact.objects.filter(source_file='f338y(feb 26 brkg).xlsx').count()
150
```

### View Table Statistics

```bash
python manage.py shell
>>> from database.models import BrokerageFact, ClientDim, EmployeeDim, MFact
>>> print(f"BrokerageFact: {BrokerageFact.objects.count()} rows")
>>> print(f"ClientDim: {ClientDim.objects.count()} rows")
>>> print(f"EmployeeDim: {EmployeeDim.objects.count()} rows")
>>> print(f"MFact: {MFact.objects.count()} rows")
```

## Troubleshooting

### Files Not Loading

**Problem**: Excel files in `data_files/` folder are not being loaded
- Check file extension is `.xlsx`, `.xls`, `.xlsm`, or `.csv`
- Check file is not corrupted (`pandas` should open it)
- Check folder path in `schema_config.yaml` matches actual folder
- Check file watcher is running: `ps aux | grep start_watcher.py`
- Check logs: `tail -f database/logs/watcher.log`

### Duplicate Rows

**Problem**: Same row appears multiple times in database
- This means different files had identical rows and hash detection failed
- Solution: Use `row_hash` field to identify duplicates
  ```python
  from django.db.models import Count
  from database.models import BrokerageFact
  
  # Find rows with same hash
  BrokerageFact.objects.values('row_hash').annotate(
      cnt=Count('id')
  ).filter(cnt__gt=1)
  ```

### Data Type Errors

**Problem**: "Cannot convert '...' to [type]" validation errors
- Ensure Excel column has correct data type
- Check schema_config.yaml data_type for the column
- Example: If date column has text like "2026-03", update to "2026-03-01"

### PostgreSQL Connection Error

**Problem**: "psycopg2: could not translate host name"
- Check `.env` has correct `POSTGRES_HOST` and `POSTGRES_PORT`
- Verify PostgreSQL is running: `psql -h localhost -U postgres`
- Check firewall allows connection to POSTGRES_HOST:POSTGRES_PORT

### Permission Denied Writing Logs

**Problem**: Cannot write to `database/logs/`
- Create directory if missing: `mkdir -p database/logs`
- Check permissions: `chmod 755 database/logs/`

## Advanced Configuration

### Custom Validation Rules

Edit `database/config/schema_config.yaml`:

```yaml
columns:
  - name: "Total Brokerage"
    db_field: "total_brokerage"
    data_type: "decimal"
    validation: "must_be_positive"  # Custom rule
```

Then update `database/utils/validator.py` to handle custom rules.

### Custom Data Transformation

Edit `database/loaders/data_loader_service.py`, method `_convert_value()`:

```python
elif column == "AUM (₹)":
    # Parse "3.29 Cr" to 3,290,000,000
    value_str = str(value).replace(' Cr', '').replace(' Lk', '')
    return float(value_str) * (10**7 if 'Cr' in str(value) else 1)
```

### Scheduled Bulk Loading

Create a Django management command (e.g., `core/management/commands/bulk_load_excel.py`):

```python
from django.core.management.base import BaseCommand
from database.loaders.data_loader_service import load_table_from_files
from database.models import BrokerageFact
import yaml

class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('database/config/schema_config.yaml') as f:
            config = yaml.safe_load(f)
        
        tables = [
            ('brokerage_fact', BrokerageFact, 'data_files/brokerage_fact'),
            ('client_dim', ClientDim, 'data_files/Client_dim'),
            # ... others
        ]
        
        for table_key, model, folder in tables:
            stats = load_table_from_files(config['tables'][table_key], model, folder)
            print(f"{table_key}: {stats['total_rows_inserted']} rows inserted")
```

Then run: `python manage.py bulk_load_excel`

## API Reference

### DataLoaderService

```python
from database.loaders.data_loader_service import DataLoaderService

loader = DataLoaderService(table_config, table_name, model_class)
success, stats = loader.load_file(file_path)

# stats = {
#     'file_name': 'brokerage.xlsx',
#     'rows_loaded': 150,
#     'rows_valid': 145,
#     'rows_inserted': 145,
#     'rows_skipped_duplicate': 5,
#     'rows_failed': 0,
#     'load_time': 2.34,
# }
```

### FolderWatcher

```python
from database.watchers.folder_watcher import setup_watchers, get_watcher
import yaml

config = yaml.safe_load(open('database/config/schema_config.yaml'))
setup_watchers(config)

watcher = get_watcher()
watcher.start()
# ... do work ...
watcher.stop()
```

### DuplicateDetector

```python
from database.utils.duplicate_detector import DuplicateDetector

# Compute hash of a row
row_hash = DuplicateDetector.compute_row_hash(
    {'name': 'John', 'age': 30},
    ['name', 'age']
)

# Find duplicates in batch
rows, dupes = DuplicateDetector.check_duplicates_in_batch(
    rows_data, column_names
)
```

## Performance Notes

- **File reading**: pandas can handle 100K+ rows efficiently
- **Validation**: Linear O(n) per column
- **Deduplication**: O(n) with hash computation
- **Database insert**: Batch insert with atomic transactions (~1000 rows/sec on typical hardware)
- **File watching**: Minimal overhead, triggers only on file changes

## Security Considerations

- `.env` file with PostgreSQL credentials should NOT be committed to git
- Use strong postgres password
- Restrict database IP access via firewall if on public server
- Validate Excel files from untrusted sources (current implementation assumes trusted data)
- SQL injection: Django ORM escapes all inputs, safe from injection
- File path traversal: Watchdog monitors only configured folders

## Future Enhancements

- [ ] Web UI for data monitoring dashboard
- [ ] Failure notifications (email, Slack, etc.)
- [ ] Batch processing with job queues (Celery)
- [ ] Data archiving and retention policies
- [ ] Incremental loading (only new/changed rows)
- [ ] Automated data cleaning/transformation rules
- [ ] Export to other formats (CSV, Parquet, etc.)
- [ ] Audit trail and data lineage tracking

---

**Last Updated**: 2026-03-10  
**Maintainer**: Development Team  
**Status**: Production Ready
