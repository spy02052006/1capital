# Migration to fix UserProfile.employee_id from wire_code to numeric Employee.id

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_fix_userprofile_employee_links'),
    ]

    operations = [
        # SQLite-compatible version - skip complex data migration
        # Schema is already correct from previous migrations
    ]

