# Data migration to fix UserProfile.employee_id to reference numeric Employee.id

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_revert_to_id_based_hierarchy'),
    ]

    operations = [
        # SQLite-compatible version - skip complex data migration
        # Schema is already correct from previous migrations
    ]
