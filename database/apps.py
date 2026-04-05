"""
Database Application
Manages PostgreSQL data loading from Excel files with real-time auto-sync
"""
from django.apps import AppConfig


class DatabaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'database'
    verbose_name = 'Database - Excel Data Loader'
