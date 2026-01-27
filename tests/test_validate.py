"""
Test JSON Schema validation functionality.

Tests ensure that validate.py correctly:
- Validates valid JSON against schemas
- Rejects invalid JSON with useful error messages
- Works with all Investment OS schemas
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.investos.validate import (
    validate_json_file,
    validate_with_schema,
    validate_portfolio_snapshot,
    validate_valuation_model,
    JSONSCHEMA_AVAILABLE
)


class TestJSONValidation(unittest.TestCase):
    """Test basic JSON file validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir)
    
    def test_valid_json_file(self):
        """Test validation of valid JSON file"""
        test_file = self.temp_dir / 'test.json'
        test_file.write_text('{"test": "data"}')
        
        result = validate_json_file(test_file)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_invalid_json_file(self):
        """Test validation of invalid JSON file"""
        test_file = self.temp_dir / 'test.json'
        test_file.write_text('{"test": invalid}')
        
        result = validate_json_file(test_file)
        self.assertFalse(result.valid)
        self.assertTrue(len(result.errors) > 0)
        self.assertIn('Invalid JSON', result.errors[0])
    
    def test_nonexistent_file(self):
        """Test validation of nonexistent file"""
        test_file = self.temp_dir / 'nonexistent.json'
        
        result = validate_json_file(test_file)
        self.assertFalse(result.valid)
        self.assertTrue(any('does not exist' in e for e in result.errors))


class TestPortfolioSnapshotValidation(unittest.TestCase):
    """Test portfolio snapshot validation"""
    
    def test_valid_snapshot(self):
        """Test validation of valid portfolio snapshot"""
        snapshot = {
            'snapshot_id': '2026-01-27-120000',
            'timestamp': '2026-01-27T12:00:00Z',
            'version': '1.0.0',
            'source': {'type': 'test'},
            'accounts': [],
            'holdings': [],
            'cash': [],
            'totals': {
                'total_market_value': 0.0,
                'total_cash': 0.0,
                'total_portfolio_value': 0.0,
                'base_currency': 'EUR'
            },
            'metadata': {}
        }
        
        result = validate_portfolio_snapshot(snapshot)
        self.assertTrue(result.valid)
    
    def test_missing_required_field(self):
        """Test validation fails with missing required field"""
        snapshot = {
            'snapshot_id': '2026-01-27-120000',
            # Missing timestamp
            'version': '1.0.0',
            'accounts': [],
            'holdings': []
        }
        
        result = validate_portfolio_snapshot(snapshot)
        self.assertFalse(result.valid)
        self.assertTrue(any('timestamp' in e for e in result.errors))


@unittest.skipIf(not JSONSCHEMA_AVAILABLE, "jsonschema not installed")
class TestSchemaValidation(unittest.TestCase):
    """Test full JSON Schema validation (requires jsonschema library)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_root = Path(__file__).parent.parent
    
    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir)
    
    def test_valid_portfolio_snapshot_against_schema(self):
        """Test that a valid snapshot passes schema validation"""
        # Create valid snapshot
        snapshot = {
            'snapshot_id': '2026-01-27-120000',
            'timestamp': '2026-01-27T12:00:00+00:00',
            'version': '1.0.0',
            'source': {
                'type': 'test',
                'file': 'test.pdf',
                'ingestion_date': '2026-01-27T12:00:00+00:00'
            },
            'accounts': [
                {
                    'account_id': 'test_account',
                    'account_name': 'Test',
                    'broker': 'Test Broker',
                    'account_type': 'taxable',
                    'currency': 'EUR'
                }
            ],
            'holdings': [
                {
                    'security_id': 'US0378331005',
                    'name': 'Apple Inc.',
                    'isin': 'US0378331005',
                    'security_type': 'other',
                    'quantity': 10.0,
                    'currency': 'USD',
                    'account_id': 'test_account',
                    'market_data': {
                        'market_value': 1750.0,
                        'currency': 'USD',
                        'price_date': '2026-01-27T12:00:00+00:00'
                    }
                }
            ],
            'cash': [],
            'totals': {
                'total_market_value': 1750.0,
                'total_cash': 0.0,
                'total_portfolio_value': 1750.0,
                'base_currency': 'EUR'
            },
            'metadata': {
                'extraction_method': 'test'
            }
        }
        
        # Write to file
        snapshot_file = self.temp_dir / 'snapshot.json'
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        # Validate against schema
        schema_path = self.repo_root / 'schema' / 'portfolio-state.schema.json'
        result = validate_with_schema(snapshot_file, schema_path)
        
        if not result.valid:
            print("\nValidation errors:")
            for error in result.errors:
                print(f"  - {error}")
        
        self.assertTrue(result.valid, "Valid snapshot should pass schema validation")
    
    def test_invalid_snapshot_fails_schema_validation(self):
        """Test that an invalid snapshot fails schema validation"""
        # Create invalid snapshot (missing required field)
        invalid_snapshot = {
            'snapshot_id': '2026-01-27-120000',
            'timestamp': '2026-01-27T12:00:00+00:00',
            'version': 'invalid-version',  # Should be semver format
            'accounts': [],
            'holdings': []
            # Missing required fields: cash, totals
        }
        
        # Write to file
        snapshot_file = self.temp_dir / 'invalid.json'
        with open(snapshot_file, 'w') as f:
            json.dump(invalid_snapshot, f, indent=2)
        
        # Validate against schema
        schema_path = self.repo_root / 'schema' / 'portfolio-state.schema.json'
        result = validate_with_schema(snapshot_file, schema_path)
        
        self.assertFalse(result.valid, "Invalid snapshot should fail schema validation")
        self.assertTrue(len(result.errors) > 0, "Should have validation errors")
    
    def test_schema_validation_error_messages(self):
        """Test that schema validation provides useful error messages"""
        # Create snapshot with wrong type
        invalid_snapshot = {
            'snapshot_id': 123,  # Should be string
            'timestamp': '2026-01-27T12:00:00+00:00',
            'version': '1.0.0',
            'source': {'type': 'test'},
            'accounts': "not-an-array",  # Should be array
            'holdings': [],
            'cash': [],
            'totals': {
                'total_market_value': "not-a-number",  # Should be number
                'total_cash': 0.0,
                'total_portfolio_value': 0.0,
                'base_currency': 'EUR'
            }
        }
        
        # Write to file
        snapshot_file = self.temp_dir / 'invalid.json'
        with open(snapshot_file, 'w') as f:
            json.dump(invalid_snapshot, f, indent=2)
        
        # Validate against schema
        schema_path = self.repo_root / 'schema' / 'portfolio-state.schema.json'
        result = validate_with_schema(snapshot_file, schema_path)
        
        self.assertFalse(result.valid)
        
        # Check that error messages contain field names
        error_text = ' '.join(result.errors)
        self.assertTrue('snapshot_id' in error_text or 'accounts' in error_text or 'total_market_value' in error_text,
                       "Error messages should reference the invalid fields")


class TestValuationModelValidation(unittest.TestCase):
    """Test valuation model validation"""
    
    def test_basic_valuation_structure(self):
        """Test basic valuation model structure validation"""
        valuation = {
            'valuation_id': 'US0378331005-2026-01-27',
            'timestamp': '2026-01-27T12:00:00Z',
            'security_id': 'US0378331005',
            'version': '1.0.0',
            'assumptions': {
                'required_return': 0.10,
                'margin_of_safety': 0.25
            },
            'valuation': {
                'intrinsic_value': 180.0,
                'methodology': 'dcf'
            }
        }
        
        result = validate_valuation_model(valuation)
        self.assertTrue(result.valid)


if __name__ == '__main__':
    unittest.main()
