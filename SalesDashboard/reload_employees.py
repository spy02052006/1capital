#!/usr/bin/env python3
"""
Script to reload employee data with correct numeric IDs from Excel file.
This uses the updated _load_employee_dimension() method from data_pipeline.
"""

import os
import sys

# Fix pandas import issue on Linux
if not hasattr(os, 'add_dll_directory'):
    os.add_dll_directory = lambda x: None

import django

# Setup Django
project_dir = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
sys.path.insert(0, project_dir)
django.setup()

from core.data_pipeline import DataPipeline
from core.models import Employee
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reload_employees():
    """Reload employee data from Excel file"""
    logger.info("Starting employee data reload...")
    
    # Clear existing employees
    count_before = Employee.objects.count()
    logger.info(f"Employees before reload: {count_before}")
    
    # Create pipeline instance
    pipeline = DataPipeline()
    
    # Load employees from Excel (this will use the new numeric ID schema)
    loaded = pipeline._load_employee_dimension(clear_existing=True)
    logger.info(f"Loaded {loaded} employee records from Excel")
    
    # Verify the reload
    count_after = Employee.objects.count()
    logger.info(f"Employees after reload: {count_after}")
    
    # Check a few records to verify IDs
    sample_employees = Employee.objects.all()[:5]
    logger.info("\nSample employee records:")
    for emp in sample_employees:
        logger.info(f"  ID={emp.id}, Name={emp.rm_name}, Manager_ID={emp.manager_id}, Wire_Code={emp.wire_code}")
    
    # Build and validate hierarchy
    logger.info("\nBuilding employee hierarchy...")
    hierarchy_count = pipeline._build_employee_hierarchy()
    logger.info(f"Validated {hierarchy_count} hierarchy relationships")
    
    logger.info("\nEmployee reload completed successfully!")

if __name__ == '__main__':
    reload_employees()
