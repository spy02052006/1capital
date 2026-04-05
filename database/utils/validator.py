"""
Data Validation Engine
Validates Excel data against schema configuration before loading to database
"""
import logging
from typing import Dict, List, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates data types, required fields, and schema compliance"""
    
    def __init__(self, schema_config: Dict[str, Any]):
        """
        Initialize validator with schema configuration
        Args:
            schema_config: Schema configuration for a specific table
        """
        self.schema_config = schema_config
        self.errors = []
    
    def validate_row(self, row_data: Dict[str, Any], row_number: int) -> tuple[bool, List[str]]:
        """
        Validate a single row of data
        Args:
            row_data: Dictionary of column_name -> value
            row_number: Row number in Excel (for error reporting)
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        for column_config in self.schema_config.get('columns', []):
            excel_col_name = column_config['name']
            db_field = column_config['db_field']
            data_type = column_config['data_type']
            nullable = column_config.get('nullable', True)
            
            value = row_data.get(excel_col_name)
            
            # Check nullable
            if value is None or (isinstance(value, str) and value.strip() == ''):
                if not nullable and column_config.get('validation') == 'must not be empty':
                    errors.append(f"Row {row_number}, {excel_col_name}: Required field is empty")
                continue
            
            # Validate data type conversion
            error = self._validate_column_type(excel_col_name, value, data_type, column_config)
            if error:
                errors.append(f"Row {row_number}: {error}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_column_type(self, column_name: str, value: Any, data_type: str, config: Dict) -> str:
        """Validate and attempt to convert value to expected data type"""
        try:
            if data_type == 'string':
                if not isinstance(value, str):
                    value = str(value)
                max_length = config.get('max_length', 255)
                if len(value) > max_length:
                    return f"{column_name}: String exceeds max length {max_length}"
            
            elif data_type == 'integer':
                if not isinstance(value, int):
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        return f"{column_name}: Cannot convert '{value}' to integer"
            
            elif data_type == 'decimal':
                if not isinstance(value, (float, Decimal, int)):
                    try:
                        Decimal(str(value))
                    except (InvalidOperation, ValueError, TypeError):
                        return f"{column_name}: Cannot convert '{value}' to decimal"
            
            elif data_type == 'date':
                if not isinstance(value, datetime):
                    try:
                        datetime.fromisoformat(str(value))
                    except (ValueError, TypeError):
                        return f"{column_name}: Cannot parse '{value}' as date"
            
            return None  # Valid
        
        except Exception as e:
            return f"{column_name}: Validation error - {str(e)}"
    
    def log_validation_errors(self, table_name: str, errors: List[str]):
        """Log validation errors to logger"""
        if errors:
            logger.error(f"Validation errors for {table_name}:")
            for error in errors[:10]:  # Log first 10 errors
                logger.error(f"  - {error}")
            if len(errors) > 10:
                logger.error(f"  ... and {len(errors) - 10} more errors")


def validate_excel_data(df_data: Dict[str, List[Any]], table_config: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate entire DataFrame worth of data
    Args:
        df_data: Dictionary where keys are column names and values are lists of values
        table_config: Table configuration from schema_config.yaml
    Returns:
        (all_valid, list_of_all_errors)
    """
    validator = DataValidator(table_config)
    all_errors = []
    all_valid = True
    
    # Convert lists to row dictionaries
    if not df_data:
        return True, []
    
    num_rows = len(next(iter(df_data.values())))
    
    for row_num in range(num_rows):
        row_data = {col: df_data[col][row_num] for col in df_data}
        is_valid, errors = validator.validate_row(row_data, row_num + 2)  # +2 because row 1 is header, +1 for 1-based
        
        if not is_valid:
            all_valid = False
            all_errors.extend(errors)
    
    if not all_valid:
        validator.log_validation_errors(table_config.get('table_name'), all_errors)
    
    return all_valid, all_errors
