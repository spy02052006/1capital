"""
Database Module
Handles PostgreSQL table creation and auto-loading Excel files from data_files folder

Module Structure:
- models/       - Django ORM models for 4 tables (brokerage_fact, client_dim, employee_dim, mf_fact)
- loaders/      - Excel file loading and data pipeline logic
- watchers/     - Real-time file system monitoring
- utils/        - Validation, duplicate detection, logging utilities
- config/       - Schema configuration (YAML)
- tests/        - Unit tests for loaders and validators
"""

default_app_config = 'database.apps.DatabaseConfig'
