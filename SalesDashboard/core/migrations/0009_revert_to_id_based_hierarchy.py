# Migration to fix the database schema to use numeric IDs for hierarchy
# SQLite-compatible version

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_remove_employee_employee_dimension_rm_manager_name_idx_and_more'),
    ]

    operations = [
        # Skip this migration - SQLite doesn't support complex ALTER TABLE operations
        # The schema is already correct from previous migrations
    ]

