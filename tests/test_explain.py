"""
Test Portfolio Change Explanation Engine - Step 6

Tests the deterministic diff and attribution logic.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.investos.explain import (
    run_explanation,
    build_holding_key,
    classify_driver,
    compute_cash_changes,
    ExplainError
)


class TestExplainEngine(unittest.TestCase):
    """Test explain attribution logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_root = Path(__file__).parent.parent
        self.fixtures_dir = self.repo_root / 'tests' / 'fixtures'
    
    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_explain_validates_snapshots(self):
        """Test that explain validates both snapshots"""
        snapshot_A = self.fixtures_dir / 'snapshot_A.json'
        snapshot_B = self.fixtures_dir / 'snapshot_B.json'
        
        self.assertTrue(snapshot_A.exists(), "snapshot_A.json must exist")
        self.assertTrue(snapshot_B.exists(), "snapshot_B.json must exist")
        
        # Run explanation (should not raise)
        report = run_explanation(
            snapshot_A_path=snapshot_A,
            snapshot_B_path=snapshot_B,
            output_dir=self.temp_dir / 'test1',
            format_type='json'
        )
        
        # Check report structure
        self.assertIn('report_id', report)
        self.assertIn('from_snapshot', report)
        self.assertIn('to_snapshot', report)
        self.assertIn('drivers', report)
        self.assertIn('warnings', report)
    
    def test_explain_detects_new_and_removed_positions(self):
        """Test detection of new and removed positions"""
        snapshot_A = self.fixtures_dir / 'snapshot_A.json'
        snapshot_B = self.fixtures_dir / 'snapshot_B.json'
        
        report = run_explanation(
            snapshot_A_path=snapshot_A,
            snapshot_B_path=snapshot_B,
            output_dir=self.temp_dir / 'test2',
            format_type='json'
        )
        
        # Snapshot B has Deutsche Bank (new position)
        # Snapshot A has 2 holdings, B has 3
        driver_types = [d['type'] for d in report['drivers']]
        
        self.assertIn('new_position', driver_types, "Should detect new position")
        
        # Check stats
        stats = report['stats']
        self.assertEqual(stats['holdings_A'], 2)
        self.assertEqual(stats['holdings_B'], 3)
        self.assertEqual(stats['added'], 1)
    
    def test_explain_classifies_price_change(self):
        """Test classification of price_change (quantity unchanged, mv changed)"""
        snapshot_A = self.fixtures_dir / 'snapshot_A.json'
        snapshot_B = self.fixtures_dir / 'snapshot_B.json'
        
        report = run_explanation(
            snapshot_A_path=snapshot_A,
            snapshot_B_path=snapshot_B,
            output_dir=self.temp_dir / 'test3',
            format_type='json'
        )
        
        # Apple: quantity 100 -> 100, mv 18000 -> 19800 (price change)
        apple_drivers = [d for d in report['drivers'] if d.get('isin') == 'US0378331005']
        self.assertTrue(len(apple_drivers) > 0, "Should find Apple driver")
        
        apple_driver = apple_drivers[0]
        self.assertEqual(apple_driver['type'], 'price_change', "Apple should be price_change")
        self.assertAlmostEqual(apple_driver['contribution_abs'], 1800.00, places=2)
    
    def test_explain_classifies_quantity_change(self):
        """Test classification of quantity_change (both quantity and mv changed)"""
        snapshot_A = self.fixtures_dir / 'snapshot_A.json'
        snapshot_B = self.fixtures_dir / 'snapshot_B.json'
        
        report = run_explanation(
            snapshot_A_path=snapshot_A,
            snapshot_B_path=snapshot_B,
            output_dir=self.temp_dir / 'test4',
            format_type='json'
        )
        
        # ETF: quantity 50 -> 60, mv 4200 -> 5100 (quantity change)
        etf_drivers = [d for d in report['drivers'] if d.get('isin') == 'IE00B4L5Y983']
        self.assertTrue(len(etf_drivers) > 0, "Should find ETF driver")
        
        etf_driver = etf_drivers[0]
        self.assertEqual(etf_driver['type'], 'quantity_change', "ETF should be quantity_change")
        self.assertAlmostEqual(etf_driver['contribution_abs'], 900.00, places=2)
    
    def test_explain_cash_change(self):
        """Test cash_change detection"""
        snapshot_A = self.fixtures_dir / 'snapshot_A.json'
        snapshot_B = self.fixtures_dir / 'snapshot_B.json'
        
        report = run_explanation(
            snapshot_A_path=snapshot_A,
            snapshot_B_path=snapshot_B,
            output_dir=self.temp_dir / 'test5',
            format_type='json'
        )
        
        # Cash: 1000 -> 500 (cash decreased by 500)
        cash_drivers = [d for d in report['drivers'] if d['type'] == 'cash_change']
        self.assertTrue(len(cash_drivers) > 0, "Should detect cash change")
        
        cash_driver = cash_drivers[0]
        self.assertAlmostEqual(cash_driver['contribution_abs'], -500.00, places=2)
    
    def test_explain_residual_present_and_small(self):
        """Test that residual is computed and should be small"""
        snapshot_A = self.fixtures_dir / 'snapshot_A.json'
        snapshot_B = self.fixtures_dir / 'snapshot_B.json'
        
        report = run_explanation(
            snapshot_A_path=snapshot_A,
            snapshot_B_path=snapshot_B,
            output_dir=self.temp_dir / 'test6',
            format_type='json'
        )
        
        # Find residual driver
        residual_drivers = [d for d in report['drivers'] if d['type'] == 'residual_unexplained']
        self.assertEqual(len(residual_drivers), 1, "Should have exactly one residual driver")
        
        residual = residual_drivers[0]['contribution_abs']
        
        # Check residual reconciles
        totals = report['totals']
        portfolio_delta = totals['delta_abs']
        
        # Sum all contributions
        total_contrib = sum(d['contribution_abs'] for d in report['drivers'])
        
        # Should equal portfolio delta
        self.assertAlmostEqual(total_contrib, portfolio_delta, places=2,
                               msg="All drivers + residual should equal portfolio delta")
        
        # Residual should be small (less than 1% of delta)
        if abs(portfolio_delta) > 0.01:
            residual_pct = abs(residual) / abs(portfolio_delta)
            self.assertLess(residual_pct, 0.01,
                            "Residual should be < 1% of portfolio delta for clean test fixtures")
    
    def test_deterministic_outputs(self):
        """Test that running explain twice produces identical numeric results"""
        snapshot_A = self.fixtures_dir / 'snapshot_A.json'
        snapshot_B = self.fixtures_dir / 'snapshot_B.json'
        
        # Run twice
        report1 = run_explanation(
            snapshot_A_path=snapshot_A,
            snapshot_B_path=snapshot_B,
            output_dir=self.temp_dir / 'run1',
            format_type='json'
        )
        
        report2 = run_explanation(
            snapshot_A_path=snapshot_A,
            snapshot_B_path=snapshot_B,
            output_dir=self.temp_dir / 'run2',
            format_type='json'
        )
        
        # Compare totals
        self.assertEqual(report1['totals']['from_total'], report2['totals']['from_total'])
        self.assertEqual(report1['totals']['to_total'], report2['totals']['to_total'])
        self.assertEqual(report1['totals']['delta_abs'], report2['totals']['delta_abs'])
        
        # Compare drivers (sort by contribution for stable comparison)
        drivers1 = sorted(report1['drivers'], key=lambda d: (d['type'], d.get('isin', '')))
        drivers2 = sorted(report2['drivers'], key=lambda d: (d['type'], d.get('isin', '')))
        
        self.assertEqual(len(drivers1), len(drivers2))
        
        for d1, d2 in zip(drivers1, drivers2):
            self.assertEqual(d1['type'], d2['type'])
            self.assertAlmostEqual(d1['contribution_abs'], d2['contribution_abs'], places=2)


if __name__ == '__main__':
    unittest.main()
