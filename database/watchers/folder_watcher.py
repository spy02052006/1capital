"""
Real-time File Watcher
Monitors data_files folders and auto-loads Excel files when they appear
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Callable, Optional
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
import django

# Setup Django if not already configured
if not django.apps.apps.ready:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SalesDashboard.settings')
    django.setup()

logger = logging.getLogger(__name__)


class ExcelFileEventHandler(FileSystemEventHandler):
    """Handles file system events for Excel files"""
    
    EXCEL_EXTENSIONS = {'.xlsx', '.xls', '.xlsm', '.csv'}
    DEBOUNCE_SECONDS = 2  # Wait 2 seconds before processing to avoid multiple triggers
    
    def __init__(self, callback: Callable[[str], None], table_name: str):
        """
        Initialize handler
        Args:
            callback: Function to call when file is detected (receives file_path)
            table_name: Name of table being watched (for logging)
        """
        super().__init__()
        self.callback = callback
        self.table_name = table_name
        self.last_processed_files = {}  # Track recently processed files
    
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            self._process_file_event(event.src_path, 'created')
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            self._process_file_event(event.src_path, 'modified')
    
    def _process_file_event(self, file_path: str, event_type: str):
        """
        Process file event - check if it's an ExcelFile and should be loaded
        Args:
            file_path: Path to file
            event_type: Type of event (created, modified)
        """
        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.EXCEL_EXTENSIONS:
            return
        
        # Check if file is still being written to (size might still be changing)
        if not self._is_file_ready(file_path):
            logger.debug(f"File not ready yet: {file_path}")
            return
        
        # Debounce: don't process the same file too frequently
        now = datetime.now()
        if file_path in self.last_processed_files:
            last_time = self.last_processed_files[file_path]
            if (now - last_time).total_seconds() < self.DEBOUNCE_SECONDS:
                logger.debug(f"Debouncing file: {file_path}")
                return
        
        self.last_processed_files[file_path] = now
        
        logger.info(f"Excel file {event_type}: {file_path}")
        logger.info(f"Triggering data load for {self.table_name}...")
        
        try:
            self.callback(file_path)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}", exc_info=True)
    
    def _is_file_ready(self, file_path: str, timeout: int = 5) -> bool:
        """
        Check if file is ready (done being written to)
        Args:
            file_path: Path to file
            timeout: Max seconds to wait
        Returns:
            True if file size is stable
        """
        try:
            size_before = os.path.getsize(file_path)
            import time
            time.sleep(0.5)
            size_after = os.path.getsize(file_path)
            return size_before == size_after
        except:
            return False


class FolderWatcher:
    """Monitors multiple Excel folders and triggers data loading"""
    
    def __init__(self):
        """Initialize watcher"""
        self.observer = None
        self.watchlist = {}  # folder_path -> {handler, callback}
    
    def watch_folder(self, folder_path: str, table_name: str, callback: Callable[[str], None]):
        """
        Start watching a folder for Excel files
        Args:
            folder_path: Path to folder to monitor
            table_name: Name of table this folder loads into (for logging)
            callback: Function to call when Excel file is detected
        """
        if not os.path.exists(folder_path):
            logger.error(f"Folder does not exist: {folder_path}")
            return False
        
        if folder_path in self.watchlist:
            logger.warning(f"Folder already being watched: {folder_path}")
            return False
        
        logger.info(f"Starting to watch folder: {folder_path} for {table_name}")
        
        handler = ExcelFileEventHandler(callback, table_name)
        self.watchlist[folder_path] = {
            'handler': handler,
            'callback': callback,
            'table_name': table_name
        }
        
        return True
    
    def start(self):
        """Start the file observer"""
        if self.observer is not None:
            logger.warning("Observer already running")
            return False
        
        self.observer = Observer()
        
        # Schedule all watched folders
        for folder_path, watch_info in self.watchlist.items():
            logger.info(f"Scheduling watch for: {folder_path} ({watch_info['table_name']})")
            self.observer.schedule(
                watch_info['handler'],
                folder_path,
                recursive=False  # Don't watch subdirectories
            )
        
        try:
            self.observer.start()
            logger.info(f"File watcher started for {len(self.watchlist)} folders")
            return True
        except Exception as e:
            logger.error(f"Failed to start observer: {str(e)}")
            return False
    
    def stop(self):
        """Stop the file observer"""
        if self.observer is None:
            logger.warning("Observer is not running")
            return
        
        logger.info("Stopping file watcher...")
        self.observer.stop()
        self.observer.join()
        self.observer = None
        logger.info("File watcher stopped")
    
    def is_running(self) -> bool:
        """Check if observer is running"""
        return self.observer is not None and self.observer.is_alive()


# Global watcher instance
_global_watcher = None


def get_watcher() -> FolderWatcher:
    """Get or create global watcher instance"""
    global _global_watcher
    if _global_watcher is None:
        _global_watcher = FolderWatcher()
    return _global_watcher


def setup_watchers(config_dict: Dict) -> bool:
    """
    Setup file watchers for all data folders
    Args:
        config_dict: Schema configuration dictionary
    Returns:
        True if setup successful
    """
    watcher = get_watcher()
    
    # Import models
    from database.models import BrokerageFact, ClientDim, EmployeeDim, MFact
    from database.loaders.data_loader_service import load_table_from_files
    
    # Mapping of table names to models and folders
    table_mappings = {
        'brokerage_fact': {
            'model': BrokerageFact,
            'folder': 'data_files/brokerage_fact',
            'config_key': 'brokerage_fact',
        },
        'client_dim': {
            'model': ClientDim,
            'folder': 'data_files/Client_dim',
            'config_key': 'client_dim',
        },
        'employee_dim': {
            'model': EmployeeDim,
            'folder': 'data_files/Employee_dim',
            'config_key': 'employee_dim',
        },
        'mf_fact': {
            'model': MFact,
            'folder': 'data_files/MF_fact',
            'config_key': 'mf_fact',
        },
    }
    
    # Get base directory for data_files
    base_dir = Path(__file__).resolve().parent.parent.parent  # database/../.. = project root
    
    # Setup watcher for each table
    for table_name, mapping in table_mappings.items():
        folder_path = str(base_dir / mapping['folder'])
        model_class = mapping['model']
        config_key = mapping['config_key']
        
        if config_key not in config_dict.get('tables', {}):
            logger.warning(f"Config not found for {table_name}")
            continue
        
        table_config = config_dict['tables'][config_key]
        
        # Define callback for this table
        def make_callback(tbl_config, model, folder):
            def callback(file_path):
                logger.info(f"Loading file {file_path} into {tbl_config.get('table_name')}")
                try:
                    load_table_from_files(tbl_config, model, folder)
                except Exception as e:
                    logger.error(f"Error during file load: {e}", exc_info=True)
            return callback
        
        callback = make_callback(table_config, model_class, folder_path)
        watcher.watch_folder(folder_path, table_name, callback)
    
    # Start watcher
    return watcher.start()
