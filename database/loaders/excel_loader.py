"""
Excel File Loader
Reads Excel files and converts them to pandas DataFrame or dictionaries
"""
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class ExcelLoader:
    """Handles reading and parsing Excel files"""
    
    SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.xlsm', '.csv'}
    
    @staticmethod
    def load_excel_file(file_path: str, sheet_name: int = 0) -> Optional[pd.DataFrame]:
        """
        Load Excel file and return as pandas DataFrame
        Args:
            file_path: Full path to Excel file
            sheet_name: Sheet index to read (default: 0 = first sheet)
        Returns:
            DataFrame or None if error
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
        
        try:
            logger.info(f"Loading Excel file: {file_path}")
            
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            logger.info(f"Successfully loaded {len(df)} rows with {len(df.columns)} columns")
            return df
        
        except Exception as e:
            logger.error(f"Error loading Excel file {file_path}: {str(e)}")
            return None
    
    @staticmethod
    def validate_file_format(file_path: str) -> bool:
        """Check if file extension is supported"""
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in ExcelLoader.SUPPORTED_EXTENSIONS:
            logger.error(f"Unsupported file format: {ext}. Supported: {ExcelLoader.SUPPORTED_EXTENSIONS}")
            return False
        return True
    
    @staticmethod
    def get_sheet_names(file_path: str) -> List[str]:
        """Get list of sheet names in Excel file"""
        try:
            if file_path.endswith('.csv'):
                return ['CSV']
            
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
        except Exception as e:
            logger.error(f"Error reading sheet names from {file_path}: {str(e)}")
            return []
    
    @staticmethod
    def dataframe_to_dict_list(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Convert DataFrame to list of dictionaries (one per row)
        Args:
            df: pandas DataFrame
        Returns:
            List of row dictionaries
        """
        # Replace NaN with None for proper null handling
        df = df.where(pd.notna(df), None)
        return df.to_dict('records')
    
    @staticmethod
    def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean column names: strip whitespace, handle duplicates
        Args:
            df: pandas DataFrame
        Returns:
            DataFrame with cleaned column names
        """
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Handle duplicate column names
        cols = pd.Series(range(len(df.columns)), index=df.columns)
        for dup in cols[cols.duplicated()].index:
            cols[dup] = ([f"{d}_{k}" for k, d in enumerate(cols[dup])],)
        
        df.columns = cols.index
        return df
    
    @staticmethod
    def infer_column_types(df: pd.DataFrame) -> Dict[str, str]:
        """
        Infer data types of DataFrame columns
        Args:
            df: pandas DataFrame
        Returns:
            Dictionary of column_name -> inferred_type
        """
        type_mapping = {
            'object': 'string',
            'int64': 'integer',
            'float64': 'decimal',
            'datetime64': 'date',
            'bool': 'boolean',
        }
        
        inferred_types = {}
        for col, dtype in df.dtypes.items():
            dtype_str = str(dtype)
            inferred_types[col] = type_mapping.get(dtype_str, 'string')
        
        return inferred_types


def load_excel_to_dict_list(file_path: str, sheet_name: int = 0) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Convenience function to load Excel file directly to list of dicts
    Args:
        file_path: Path to Excel file
        sheet_name: Sheet index to load
    Returns:
        (list_of_dicts, error_message)
    """
    if not ExcelLoader.validate_file_format(file_path):
        return None, f"Unsupported file format: {file_path}"
    
    df = ExcelLoader.load_excel_file(file_path, sheet_name)
    if df is None:
        return None, f"Failed to load Excel file: {file_path}"
    
    df = ExcelLoader.clean_column_names(df)
    
    rows = ExcelLoader.dataframe_to_dict_list(df)
    return rows, None
