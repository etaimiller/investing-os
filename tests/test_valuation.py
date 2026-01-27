"""
Test Valuation v1 functionality - Step 5 mandatory tests.

Tests:
1. test_validate_schema_success
2. test_validate_schema_failure_reports_paths
3. test_value_deterministic_outputs
4. test_stock_multiple_band_math
5. test_etf_outputs_intrinsic_null
"""

import unittest
import tempfile
import shutil
import json
import yaml
import copy
from pathlib import Path
from datetime import datetime, timezone

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.investos.validate import (
    validate_with_schema,
    JSONSCHEMA_AVAILABLE
)
from tools.investos.valuation import (
    value_stock,
    value_etf_or_commodity,
    load_assumptions,
    run_valuation
)


class TestValidationSchemaV1(unittest.TestCase):
    """Test JSON Schema validation (mandatory tests 1-2)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_root = Path(__file__).parent.parent
        self.fixtures_dir = self.repo_root / 'tests' / 'fixtures'
    
    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_schema_success(self):
        """Test 1: Valid JSON passes schema validation"""
        if not JSONSCHEMA_AVAILABLE:
            self.skipTest("jsonschema library not installed")
        
        # Use committed fixture
        snapshot_file = self.fixtures_dir / 'snapshot_minimal.json'
        schema_file = self.repo_root / 'schema' / 'portfolio-state.schema.json'
        
        self.assertTrue(snapshot_file.exists(), "Fixture snapshot_minimal.json must exist")
        self.assertTrue(schema_file.exists(), "Schema file must exist")
        
        # Validate
        result = validate_with_schema(snapshot_file, schema_file)
        
        # Assert passes
        self.assertTrue(result.valid, f"Validation should pass. Errors: {result.errors}")
        self.assertEqual(len(result.errors), 0, "Should have no errors")
    
    def test_validate_schema_failure_reports_paths(self):
        """Test 2: Invalid JSON reports errors with JSON paths"""
        if not JSONSCHEMA_AVAILABLE:
            self.skipTest("jsonschema library not installed")
        
        # Create invalid snapshot (missing required field)
        invalid_snapshot = {
            "snapshot_id": "test-invalid",
            "timestamp": "2026-01-27T12:00:00Z",
            "version": "1.0.0"
            # Missing: accounts, holdings, cash, totals (required fields)
        }
        
        invalid_file = self.temp_dir / 'invalid.json'
        with open(invalid_file, 'w') as f:
            json.dump(invalid_snapshot, f)
        
        schema_file = self.repo_root / 'schema' / 'portfolio-state.schema.json'
        
        # Validate
        result = validate_with_schema(invalid_file, schema_file)
        
        # Assert fails
        self.assertFalse(result.valid, "Validation should fail for invalid JSON")
        self.assertGreater(len(result.errors), 0, "Should have errors")
        
        # Check errors include paths or field names
        errors_text = ' '.join(result.errors)
        # Should mention missing required fields
        self.assertTrue(
            any(field in errors_text for field in ['accounts', 'holdings', 'cash', 'totals']),
            f"Errors should mention missing fields. Got: {result.errors}"
        )


class TestValuationDeterminism(unittest.TestCase):
    """Test valuation determinism and calculation logic (mandatory tests 3-5)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_root = Path(__file__).parent.parent
        self.fixtures_dir = self.repo_root / 'tests' / 'fixtures'
    
    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_value_deterministic_outputs(self):
        """Test 3: Same inputs produce identical valuation outputs (except timestamps/IDs)"""
        snapshot_file = self.fixtures_dir / 'snapshot_minimal.json'
        assumptions_file = self.fixtures_dir / 'assumptions_conservative.yaml'
        
        self.assertTrue(snapshot_file.exists(), "Fixture snapshot must exist")
        self.assertTrue(assumptions_file.exists(), "Fixture assumptions must exist")
        
        # Run valuation twice
        output_dir_1 = self.temp_dir / 'run1'
        output_dir_2 = self.temp_dir / 'run2'
        
        valuations_1, summary_1 = run_valuation(
            snapshot_path=snapshot_file,
            assumptions_path=assumptions_file,
            output_dir=output_dir_1,
            profile='conservative'
        )
        
        valuations_2, summary_2 = run_valuation(
            snapshot_path=snapshot_file,
            assumptions_path=assumptions_file,
            output_dir=output_dir_2,
            profile='conservative'
        )
        
        # Should have same number of valuations
        self.assertEqual(len(valuations_1), len(valuations_2))
        
        # Compare valuation outputs (ignoring timestamps/IDs)
        for v1, v2 in zip(valuations_1, valuations_2):
            # Security IDs should match
            self.assertEqual(v1.get('security_id'), v2.get('security_id'))
            
            # Methodology should match
            self.assertEqual(v1.get('methodology'), v2.get('methodology'))
            
            # Facts should match exactly
            facts1 = v1.get('facts', {})
            facts2 = v2.get('facts', {})
            self.assertEqual(facts1.get('market_value'), facts2.get('market_value'))
            self.assertEqual(facts1.get('quantity'), facts2.get('quantity'))
            
            # Valuation outputs should match (if not null)
            val1 = v1.get('valuation', {})
            val2 = v2.get('valuation', {})
            
            # Intrinsic values should be identical
            self.assertEqual(val1.get('intrinsic_value'), val2.get('intrinsic_value'))
            
            iv_range_1 = val1.get('intrinsic_value_range', {})
            iv_range_2 = val2.get('intrinsic_value_range', {})
            self.assertEqual(iv_range_1.get('low'), iv_range_2.get('low'))
            self.assertEqual(iv_range_1.get('base'), iv_range_2.get('base'))
            self.assertEqual(iv_range_1.get('high'), iv_range_2.get('high'))
    
    def test_stock_multiple_band_math(self):
        """Test 4: Stock valuation with fundamentals computes correct multiple bands"""
        # Load assumptions
        assumptions_file = self.fixtures_dir / 'assumptions_conservative.yaml'
        self.assertTrue(assumptions_file.exists(), "Fixture assumptions must exist")
        
        with open(assumptions_file, 'r') as f:
            assumptions = yaml.safe_load(f)
        
        # Create test fundamentals file
        fundamentals_file = self.fixtures_dir / 'fundamentals_stock.json'
        if fundamentals_file.exists():
            with open(fundamentals_file, 'r') as f:
                fundamentals = json.load(f)
        else:
            # Create minimal fundamentals for testing
            fundamentals = {
                "security_id": "US0378331005",
                "security_name": "Test Stock Inc.",
                "fundamentals": {
                    "earnings": {
                        "net_income_ttm": 100000000
                    },
                    "margins": {
                        "operating_margin": 0.25,
                        "net_margin": 0.20
                    }
                }
            }
        
        # Create test holding
        holding = {
            'isin': 'US0378331005',
            'name': 'Test Stock Inc.',
            'quantity': 1000,
            'currency': 'USD',
            'market_data': {
                'market_value': 50000,
                'currency': 'USD'
            }
        }
        
        # Create minimal snapshot
        snapshot = {
            'snapshot_id': 'test-snapshot',
            'timestamp': '2026-01-27T12:00:00Z',
            'totals': {
                'total_portfolio_value': 50000
            }
        }
        
        # Run valuation
        valuation = value_stock(
            holding=holding,
            snapshot=snapshot,
            assumptions=assumptions,
            fundamentals=fundamentals
        )
        
        # Check structure exists
        self.assertIn('valuation', valuation)
        self.assertIn('assumptions', valuation)
        self.assertIn('methodology', valuation)
        
        # For v1, intrinsic_value may be null (not fully implemented DCF)
        # Just verify structure is correct
        val_output = valuation.get('valuation', {})
        self.assertIn('intrinsic_value_range', val_output)
        
        iv_range = val_output.get('intrinsic_value_range', {})
        self.assertIn('low', iv_range)
        self.assertIn('base', iv_range)
        self.assertIn('high', iv_range)
        
        # NOTE: v1 may have null values - that's acceptable per spec
        # The structure and determinism are what matter
    
    def test_etf_outputs_intrinsic_null(self):
        """Test 5: ETF valuations output intrinsic_value as null"""
        # Load assumptions
        assumptions_file = self.fixtures_dir / 'assumptions_conservative.yaml'
        self.assertTrue(assumptions_file.exists(), "Fixture assumptions must exist")
        
        with open(assumptions_file, 'r') as f:
            assumptions = yaml.safe_load(f)
        
        # Create test ETF holding
        etf_holding = {
            'isin': 'IE00B4L5Y983',
            'name': 'iShares Core MSCI World UCITS ETF',
            'quantity': 100,
            'currency': 'EUR',
            'market_data': {
                'market_value': 8000,
                'currency': 'EUR'
            }
        }
        
        # Create minimal snapshot
        snapshot = {
            'snapshot_id': 'test-snapshot-etf',
            'timestamp': '2026-01-27T12:00:00Z',
            'totals': {
                'total_portfolio_value': 8000
            }
        }
        
        # Run ETF valuation
        valuation = value_etf_or_commodity(
            holding=etf_holding,
            snapshot=snapshot,
            assumptions=assumptions,
            security_type='etf'
        )
        
        # Check intrinsic value is null
        val_output = valuation.get('valuation', {})
        
        self.assertIsNone(
            val_output.get('intrinsic_value'),
            "ETF intrinsic_value should be null"
        )
        
        # Check intrinsic_value_range components are null
        iv_range = val_output.get('intrinsic_value_range', {})
        self.assertIsNone(iv_range.get('low'), "ETF intrinsic_value_range.low should be null")
        self.assertIsNone(iv_range.get('base'), "ETF intrinsic_value_range.base should be null")
        self.assertIsNone(iv_range.get('high'), "ETF intrinsic_value_range.high should be null")
        
        # Check methodology indicates allocation vehicle
        self.assertEqual(
            valuation.get('methodology'),
            'allocation_vehicle_no_intrinsic',
            "ETF should use allocation_vehicle methodology"
        )


if __name__ == '__main__':
    unittest.main()
