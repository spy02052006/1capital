#!/usr/bin/env python
"""
Start Database File Watcher
Monitors data_files folders and auto-loads Excel files to PostgreSQL

Usage:
    python database/start_watcher.py
"""
import os
import sys
import django
import yaml
import logging
from pathlib import Path

# Add SalesDashboard folder to path
project_root = Path(__file__).resolve().parent.parent
sales_dashboard_dir = project_root / 'SalesDashboard'
sys.path.insert(0, str(sales_dashboard_dir))
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
os.chdir(str(sales_dashboard_dir))
django.setup()

# Setup logging
log_dir = project_root / 'database' / 'logs'
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(log_dir / 'watcher.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from database.watchers.folder_watcher import setup_watchers, get_watcher


def load_schema_config():
    """Load schema configuration from YAML"""
    config_path = Path(__file__).resolve().parent / 'config' / 'schema_config.yaml'
    
    if not config_path.exists():
        logger.error(f"Schema config not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded schema config from {config_path}")
    return config


def main():
    """Main entry point for file watcher"""
    logger.info("\n" + "="*70)
    logger.info("Database File Watcher Starting")
    logger.info("="*70)
    
    # Load configuration
    config = load_schema_config()
    
    # Setup watchers for all tables
    success = setup_watchers(config)
    if not success:
        logger.error("Failed to setup file watchers")
        sys.exit(1)
    
    logger.info("File watchers ready. Monitoring for Excel files...")
    logger.info("Press Ctrl+C to stop.\n")
    
    # Keep running
    watcher = get_watcher()
    try:
        while watcher.is_running():
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nShutting down file watcher...")
        watcher.stop()
        logger.info("File watcher stopped.")
        sys.exit(0)


if __name__ == '__main__':
    main()
