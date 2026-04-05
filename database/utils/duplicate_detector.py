"""
Duplicate Detection Engine
Uses row hashing to detect and skip duplicate records
"""
import hashlib
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Detects duplicate rows using SHA256 hashing of all columns"""
    
    @staticmethod
    def compute_row_hash(row_data: Dict[str, Any], columns: List[str]) -> str:
        """
        Compute SHA256 hash of all column values in a row
        Args:
            row_data: Dictionary of column_name -> value
            columns: List of column names to include in hash
        Returns:
            Hex-encoded SHA256 hash
        """
        hash_input = ""
        
        for column in columns:
            value = row_data.get(column, '')
            
            # Convert all values to string and normalize
            if value is None:
                value_str = "NULL"
            elif isinstance(value, (int, float)):
                value_str = str(value)
            elif isinstance(value, bytes):
                value_str = value.decode('utf-8', errors='ignore')
            else:
                value_str = str(value).strip()
            
            hash_input += value_str + "|"
        
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    @staticmethod
    def check_duplicates_in_batch(rows_data: List[Dict[str, Any]], columns: List[str]) -> Tuple[List[Dict], List[str]]:
        """
        Check for duplicates within a batch of rows
        Args:
            rows_data: List of row dictionaries
            columns: Columns to use for hash computation
        Returns:
            (unique_rows, duplicate_hashes)
        """
        seen_hashes = set()
        unique_rows = []
        duplicate_hashes = []
        
        for row in rows_data:
            row_hash = DuplicateDetector.compute_row_hash(row, columns)
            
            if row_hash not in seen_hashes:
                seen_hashes.add(row_hash)
                unique_rows.append(row)
            else:
                duplicate_hashes.append(row_hash)
        
        if duplicate_hashes:
            logger.warning(f"Found {len(duplicate_hashes)} duplicate rows within batch")
        
        return unique_rows, duplicate_hashes
    
    @staticmethod
    def check_duplicates_against_db(rows_data: List[Dict[str, Any]], columns: List[str], 
                                    model_class) -> Tuple[List[Dict], List[Dict]]:
        """
        Check if rows already exist in database
        Args:
            rows_data: List of row dictionaries
            columns: Columns to use for hash computation
            model_class: Django model class to query
        Returns:
            (new_rows, existing_rows_info)
        """
        new_rows = []
        existing_rows = []
        
        # Get all existing row hashes from database
        existing_hashes = set(
            model_class.objects.filter(row_hash__isnull=False)
            .values_list('row_hash', flat=True)
        )
        
        for row in rows_data:
            row_hash = DuplicateDetector.compute_row_hash(row, columns)
            row['_computed_hash'] = row_hash
            
            if row_hash in existing_hashes:
                existing_rows.append({
                    'hash': row_hash,
                    'sample': str(row_data)[:100]
                })
            else:
                new_rows.append(row)
        
        if existing_rows:
            logger.info(f"Skipping {len(existing_rows)} duplicate rows already in database")
        
        return new_rows, existing_rows


def deduplicate_batch(batch_data: List[Dict[str, Any]], all_columns: List[str]) -> Tuple[List[Dict], Dict[str, Any]]:
    """
    Deduplicate a batch of rows (within batch + against database)
    Args:
        batch_data: List of row dictionaries
        all_columns: All column names for hashing
    Returns:
        (clean_rows, dedup_stats)
    """
    stats = {
        'total_input': len(batch_data),
        'duplicates_within_batch': 0,
        'duplicates_in_db': 0,
        'final_count': 0,
    }
    
    # First, remove duplicates within the batch
    unique_rows, within_batch_dupes = DuplicateDetector.check_duplicates_in_batch(
        batch_data, all_columns
    )
    stats['duplicates_within_batch'] = len(within_batch_dupes)
    
    # No need to check DB yet - that happens during actual insert
    # Just return the unique rows
    clean_rows = unique_rows
    stats['final_count'] = len(clean_rows)
    
    return clean_rows, stats
