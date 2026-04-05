"""
Unit tests for database loaders and validators
Run with: python manage.py test database.tests
"""
import os
import tempfile
from io import BytesIO
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
import pandas as pd

from database.loaders.excel_loader import ExcelLoader, load_excel_to_dict_list
from database.utils.validator import DataValidator
from database.utils.duplicate_detector import DuplicateDetector
from database.models import BrokerageFact, ClientDim


class ExcelLoaderTests(TestCase):
    """Test Excel file reading and parsing"""
    
    def test_validate_file_format(self):
        """Test that valid Excel formats are recognized"""
        self.assertTrue(ExcelLoader.validate_file_format('test.xlsx'))
        self.assertTrue(ExcelLoader.validate_file_format('test.xls'))
        self.assertTrue(ExcelLoader.validate_file_format('test.csv'))
        self.assertFalse(ExcelLoader.validate_file_format('test.txt'))
        self.assertFalse(ExcelLoader.validate_file_format('test.pdf'))
    
    def test_dataframe_to_dict_list(self):
        """Test DataFrame to dict list conversion"""
        df = pd.DataFrame({
            'Name': ['John', 'Jane'],
            'Age': [30, 25],
            'Score': [85.5, 92.3]
        })
        
        result = ExcelLoader.dataframe_to_dict_list(df)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['Name'], 'John')
        self.assertEqual(result[0]['Age'], 30)
        self.assertEqual(result[1]['Name'], 'Jane')
    
    def test_clean_column_names(self):
        """Test column name cleaning (strip whitespace)"""
        df = pd.DataFrame({
            ' Name  ': [1, 2],
            '  ID': [3, 4],
            'Score ': [5, 6]
        })
        
        cleaned = ExcelLoader.clean_column_names(df)
        
        self.assertIn('Name', cleaned.columns)
        self.assertIn('ID', cleaned.columns)
        self.assertIn('Score', cleaned.columns)


class ValidatorTests(TestCase):
    """Test data validation logic"""
    
    def setUp(self):
        """Setup test schema configuration"""
        self.schema = {
            'table_name': 'TestTable',
            'columns': [
                {
                    'name': 'Name',
                    'db_field': 'name',
                    'data_type': 'string',
                    'max_length': 100,
                    'nullable': False,
                    'validation': 'must not be empty'
                },
                {
                    'name': 'Age',
                    'db_field': 'age',
                    'data_type': 'integer',
                    'nullable': True
                },
                {
                    'name': 'Amount',
                    'db_field': 'amount',
                    'data_type': 'decimal',
                    'nullable': True
                },
                {
                    'name': 'Date',
                    'db_field': 'date',
                    'data_type': 'date',
                    'nullable': True
                }
            ]
        }
    
    def test_validate_valid_row(self):
        """Test validation of valid row"""
        validator = DataValidator(self.schema)
        row = {
            'Name': 'John Smith',
            'Age': 30,
            'Amount': 100.50,
            'Date': '2026-03-10'
        }
        
        is_valid, errors = validator.validate_row(row, 2)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_empty_required_field(self):
        """Test validation fails for empty required field"""
        validator = DataValidator(self.schema)
        row = {
            'Name': '',  # Required field, empty
            'Age': 30,
            'Amount': 100.50,
            'Date': '2026-03-10'
        }
        
        is_valid, errors = validator.validate_row(row, 2)
        
        self.assertFalse(is_valid)
        self.assertTrue(any('Name' in e for e in errors))
    
    def test_validate_type_mismatch(self):
        """Test validation catches type mismatches"""
        validator = DataValidator(self.schema)
        row = {
            'Name': 'John',
            'Age': 'thirty',  # Should be integer
            'Amount': 100.50,
            'Date': '2026-03-10'
        }
        
        is_valid, errors = validator.validate_row(row, 2)
        
        self.assertFalse(is_valid)
        self.assertTrue(any('Age' in e for e in errors))


class DuplicateDetectorTests(TestCase):
    """Test duplicate detection logic"""
    
    def test_compute_row_hash(self):
        """Test row hash computation"""
        row = {'name': 'John', 'age': 30}
        columns = ['name', 'age']
        
        hash1 = DuplicateDetector.compute_row_hash(row, columns)
        hash2 = DuplicateDetector.compute_row_hash(row, columns)
        
        # Same input should produce same hash
        self.assertEqual(hash1, hash2)
        # Hash should be hex string of length 64 (SHA256)
        self.assertEqual(len(hash1), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash1))
    
    def test_hash_different_for_different_data(self):
        """Test that different data produces different hashes"""
        row1 = {'name': 'John', 'age': 30}
        row2 = {'name': 'Jane', 'age': 30}
        columns = ['name', 'age']
        
        hash1 = DuplicateDetector.compute_row_hash(row1, columns)
        hash2 = DuplicateDetector.compute_row_hash(row2, columns)
        
        self.assertNotEqual(hash1, hash2)
    
    def test_deduplicate_batch(self):
        """Test deduplication within batch"""
        rows = [
            {'name': 'John', 'age': 30},
            {'name': 'Jane', 'age': 25},
            {'name': 'John', 'age': 30},  # Duplicate of row 1
        ]
        columns = ['name', 'age']
        
        unique_rows, stats = DuplicateDetector.check_duplicates_in_batch(rows, columns)
        
        self.assertEqual(len(unique_rows), 2)
        self.assertEqual(stats['duplicates_within_batch'], 1)


class BrokerageFact ModelTests(TestCase):
    """Test BrokerageFact model operations"""
    
    def test_create_record(self):
        """Test creating a BrokerageFact record"""
        record = BrokerageFact.objects.create(
            client_code='TEST001',
            wire_code='WC001',
            transaction_date='2026-03-10',
            cash_delivery=Decimal('1000.00'),
            total_brokerage=Decimal('50.00'),
            source_file='test.xlsx'
        )
        
        self.assertIsNotNone(record.id)
        self.assertEqual(record.client_code, 'TEST001')
        self.assertEqual(record.cash_delivery, Decimal('1000.00'))
    
    def test_record_metadata(self):
        """Test that metadata fields are automatically set"""
        record = BrokerageFact.objects.create(
            client_code='TEST002',
            wire_code='WC002',
            transaction_date='2026-03-10',
            source_file='test.xlsx'
        )
        
        self.assertIsNotNone(record.loaded_at)
        self.assertIsNotNone(record.updated_at)


class ClientDim ModelTests(TestCase):
    """Test ClientDim model operations"""
    
    def test_unique_client_id(self):
        """Test that client_id_pan is unique"""
        ClientDim.objects.create(
            client_id_pan='PAN001',
            client_name='Test Client 1'
        )
        
        # Attempting to create duplicate should raise error
        with self.assertRaises(Exception):  # IntegrityError
            ClientDim.objects.create(
                client_id_pan='PAN001',
                client_name='Test Client 2'
            )


# Integration test helpers
def create_test_excel_file(filename, data_dict):
    """Helper to create test Excel file"""
    df = pd.DataFrame(data_dict)
    df.to_excel(filename, index=False)
    return filename


def cleanup_test_files(files):
    """Helper to cleanup test files"""
    for f in files:
        if os.path.exists(f):
            os.remove(f)
