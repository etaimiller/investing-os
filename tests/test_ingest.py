"""
Test ingestion module using mocked parsed data.

Since we cannot commit real Trade Republic PDFs, these tests use
mocked parsed data structures to verify the snapshot creation logic.
"""

import unittest
import json
from pathlib import Path
from datetime import datetime, timezone
import sys
import tempfile
import shutil

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.investos.ingest import create_canonical_snapshot
from tools.investos.validate import validate_with_schema, JSONSCHEMA_AVAILABLE


class TestSnapshotCreation(unittest.TestCase):
    """Test canonical snapshot creation from parsed data"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Mock parsed data matching what parser would return
        self.mock_parsed_data = {
            'holdings': [
                {
                    'security_id': 'US0378331005',
                    'isin': 'US0378331005',
                    'name': 'Apple Inc.',
                    'quantity': 10.0,
                    'currency': 'USD',
                    'cost_basis': {
                        'average_price': 150.00,
                        'total_cost': 1500.00,
                        'currency': 'USD'
                    },
                    'market_data': {
                        'price': 175.50,
                        'market_value': 1755.00,
                        'currency': 'USD'
                    }
                },
                {
                    'security_id': 'IE00B4L5Y983',
                    'isin': 'IE00B4L5Y983',
                    'name': 'iShares Core MSCI World UCITS ETF',
                    'quantity': 50.0,
                    'currency': 'EUR',
                    'cost_basis': {
                        'average_price': 70.00,
                        'total_cost': 3500.00,
                        'currency': 'EUR'
                    },
                    'market_data': {
                        'price': 75.25,
                        'market_value': 3762.50,
                        'currency': 'EUR'
                    }
                }
            ],
            'cash': [
                {
                    'currency': 'EUR',
                    'amount': 1234.56,
                    'cash_type': 'available'
                }
            ],
            'warnings': [],
            'metadata': {
                'source_pdf': 'test_portfolio.pdf',
                'pdf_pages': 1,
                'extraction_method': 'test'
            }
        }
        
    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir)
    
    def test_snapshot_structure(self):
        """Test that snapshot has required fields"""
        source_pdf = self.temp_dir / 'test.pdf'
        source_pdf.touch()
        
        snapshot = create_canonical_snapshot(
            self.mock_parsed_data,
            source_pdf,
            'test_account'
        )
        
        # Check required top-level keys
        required_keys = ['snapshot_id', 'timestamp', 'version', 'source', 
                        'accounts', 'holdings', 'cash', 'totals', 'metadata']
        for key in required_keys:
            self.assertIn(key, snapshot, f"Missing required key: {key}")
    
    def test_snapshot_id_format(self):
        """Test snapshot ID format"""
        source_pdf = self.temp_dir / 'test.pdf'
        source_pdf.touch()
        
        snapshot = create_canonical_snapshot(
            self.mock_parsed_data,
            source_pdf,
            'test_account'
        )
        
        # Snapshot ID should be YYYY-MM-DD-HHMMSS format
        snapshot_id = snapshot['snapshot_id']
        self.assertRegex(snapshot_id, r'\d{4}-\d{2}-\d{2}-\d{6}')
    
    def test_holdings_count(self):
        """Test holdings are correctly transferred"""
        source_pdf = self.temp_dir / 'test.pdf'
        source_pdf.touch()
        
        snapshot = create_canonical_snapshot(
            self.mock_parsed_data,
            source_pdf,
            'test_account'
        )
        
        self.assertEqual(len(snapshot['holdings']), 2)
        self.assertEqual(len(snapshot['cash']), 1)
    
    def test_totals_calculation(self):
        """Test portfolio totals are calculated"""
        source_pdf = self.temp_dir / 'test.pdf'
        source_pdf.touch()
        
        snapshot = create_canonical_snapshot(
            self.mock_parsed_data,
            source_pdf,
            'test_account'
        )
        
        # Check totals
        self.assertIn('total_market_value', snapshot['totals'])
        self.assertIn('total_cash', snapshot['totals'])
        self.assertIn('total_portfolio_value', snapshot['totals'])
        
        # Total cash should match
        self.assertAlmostEqual(snapshot['totals']['total_cash'], 1234.56)
        
        # Total market value should be sum of holdings
        expected_market_value = 1755.00 + 3762.50
        self.assertAlmostEqual(snapshot['totals']['total_market_value'], expected_market_value)
    
    def test_account_assignment(self):
        """Test holdings are assigned to account"""
        source_pdf = self.temp_dir / 'test.pdf'
        source_pdf.touch()
        
        snapshot = create_canonical_snapshot(
            self.mock_parsed_data,
            source_pdf,
            'main'
        )
        
        # All holdings should have account_id
        for holding in snapshot['holdings']:
            self.assertIn('account_id', holding)
            self.assertEqual(holding['account_id'], 'trade_republic_main')
    
    def test_json_serializable(self):
        """Test snapshot can be serialized to JSON"""
        source_pdf = self.temp_dir / 'test.pdf'
        source_pdf.touch()
        
        snapshot = create_canonical_snapshot(
            self.mock_parsed_data,
            source_pdf,
            'test_account'
        )
        
        # Should be able to serialize
        try:
            json_str = json.dumps(snapshot, default=str)
            self.assertIsInstance(json_str, str)
        except (TypeError, ValueError) as e:
            self.fail(f"Snapshot not JSON serializable: {e}")


class TestParsingContract(unittest.TestCase):
    """Test the contract between parser and snapshot creator"""
    
    def test_handles_missing_cost_basis(self):
        """Test snapshot creation when cost basis is missing"""
        parsed_data = {
            'holdings': [
                {
                    'security_id': 'US0378331005',
                    'isin': 'US0378331005',
                    'name': 'Apple Inc.',
                    'quantity': 10.0,
                    'currency': 'USD',
                    'cost_basis': None,  # Missing
                    'market_data': {
                        'price': 175.50,
                        'market_value': 1755.00,
                        'currency': 'USD'
                    }
                }
            ],
            'cash': [],
            'warnings': ['Could not extract cost basis'],
            'metadata': {}
        }
        
        source_pdf = Path('/tmp/test.pdf')
        snapshot = create_canonical_snapshot(parsed_data, source_pdf)
        
        # Should still create snapshot
        self.assertEqual(len(snapshot['holdings']), 1)
        # cost_basis key should not be present or be None
        holding = snapshot['holdings'][0]
        if 'cost_basis' in holding:
            self.assertIsNone(holding['cost_basis'])
    
    def test_handles_missing_market_data(self):
        """Test snapshot creation when market data is missing"""
        parsed_data = {
            'holdings': [
                {
                    'security_id': 'US0378331005',
                    'isin': 'US0378331005',
                    'name': 'Apple Inc.',
                    'quantity': 10.0,
                    'currency': 'USD',
                    'cost_basis': {
                        'average_price': 150.00,
                        'total_cost': 1500.00,
                        'currency': 'USD'
                    },
                    'market_data': None  # Missing
                }
            ],
            'cash': [],
            'warnings': ['Could not extract current prices'],
            'metadata': {}
        }
        
        source_pdf = Path('/tmp/test.pdf')
        snapshot = create_canonical_snapshot(parsed_data, source_pdf)
        
        # Should still create snapshot
        self.assertEqual(len(snapshot['holdings']), 1)
        # market_data key should not be present or be None
        holding = snapshot['holdings'][0]
        if 'market_data' in holding:
            self.assertIsNone(holding['market_data'])


class TestFixtureValidation(unittest.TestCase):
    """Test that committed fixtures validate against schemas"""
    
    def test_sample_snapshot_validates(self):
        """Test that fixtures/sample_snapshot.json validates against schema"""
        if not JSONSCHEMA_AVAILABLE:
            self.skipTest("jsonschema not installed")
        
        repo_root = Path(__file__).parent.parent
        fixture_path = repo_root / 'fixtures' / 'sample_snapshot.json'
        schema_path = repo_root / 'schema' / 'portfolio-state.schema.json'
        
        self.assertTrue(fixture_path.exists(), "Sample fixture should exist")
        self.assertTrue(schema_path.exists(), "Portfolio schema should exist")
        
        result = validate_with_schema(fixture_path, schema_path)
        
        if not result.valid:
            self.fail(f"Sample fixture validation failed:\n" + "\n".join(result.errors))
        
        self.assertTrue(result.valid, "Sample snapshot should validate against schema")


class TestSnapshotSchemaCompliance(unittest.TestCase):
    """Test that generated snapshots comply with schema"""
    
    @unittest.skipIf(not JSONSCHEMA_AVAILABLE, "jsonschema not installed")
    def test_generated_snapshot_validates_against_schema(self):
        """Test that create_canonical_snapshot produces schema-compliant output"""
        # Mock parsed data
        parsed_data = {
            'holdings': [
                {
                    'security_id': 'US0000000001',
                    'isin': 'US0000000001',
                    'name': 'Test Corp',
                    'quantity': 10.0,
                    'currency': 'USD',
                    'cost_basis': {
                        'average_price': 100.00,
                        'total_cost': 1000.00,
                        'currency': 'USD'
                    },
                    'market_data': {
                        'price': 110.00,
                        'market_value': 1100.00,
                        'currency': 'USD'
                    }
                }
            ],
            'cash': [
                {
                    'currency': 'EUR',
                    'amount': 500.00,
                    'cash_type': 'available'
                }
            ],
            'warnings': [],
            'metadata': {}
        }
        
        # Create snapshot
        temp_dir = Path(tempfile.mkdtemp())
        try:
            source_pdf = temp_dir / 'test.pdf'
            source_pdf.touch()
            
            snapshot = create_canonical_snapshot(parsed_data, source_pdf, 'test')
            
            # Write to temp file
            snapshot_file = temp_dir / 'snapshot.json'
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot, f, default=str)
            
            # Validate against schema
            repo_root = Path(__file__).parent.parent
            schema_path = repo_root / 'schema' / 'portfolio-state.schema.json'
            
            result = validate_with_schema(snapshot_file, schema_path)
            
            if not result.valid:
                self.fail(
                    f"Generated snapshot failed schema validation:\n" + 
                    "\n".join(result.errors[:5])  # Show first 5 errors
                )
            
            self.assertTrue(result.valid, "Generated snapshot should be schema-compliant")
        
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
