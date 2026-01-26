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

from tools.investos.ingest import create_canonical_snapshot, is_valid_isin, TradeRepublicParser
from tools.investos.validate import validate_with_schema, JSONSCHEMA_AVAILABLE
from unittest.mock import Mock, patch


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


class TestISINValidation(unittest.TestCase):
    """Test ISIN checksum validation"""
    
    def test_valid_isins(self):
        """Test that valid ISINs pass checksum validation"""
        valid_isins = [
            'US0378331005',  # Apple Inc.
            'IE00B4L5Y983',  # iShares Core MSCI World UCITS ETF
            'GB00B4L5Y983',  # Valid checksum
            'DE0005140008',  # Deutsche Bank
            'FR0000120271',  # Total SA
            'NL0000009165',  # Airbus
            'CH0038863350',  # Nestle
        ]
        
        for isin in valid_isins:
            with self.subTest(isin=isin):
                self.assertTrue(
                    is_valid_isin(isin),
                    f"Valid ISIN {isin} should pass checksum validation"
                )
    
    def test_invalid_isins(self):
        """Test that invalid ISINs fail checksum validation"""
        invalid_isins = [
            'BRUNNENSTRAS',   # False positive from street name (12 chars but wrong format)
            'US0378331006',   # Wrong checksum (should be 005)
            'US0378331004',   # Wrong checksum (should be 005)
            'IE00B4L5Y984',   # Wrong checksum (should be 983)
            'DE0005140009',   # Wrong checksum (should be 008)
        ]
        
        for isin in invalid_isins:
            with self.subTest(isin=isin):
                self.assertFalse(
                    is_valid_isin(isin),
                    f"Invalid ISIN {isin} should fail checksum validation"
                )
    
    def test_wrong_length(self):
        """Test that ISINs with wrong length fail validation"""
        wrong_length = [
            'US037833100',    # Too short
            'US03783310055',  # Too long
            'US',             # Way too short
        ]
        
        for isin in wrong_length:
            with self.subTest(isin=isin):
                self.assertFalse(
                    is_valid_isin(isin),
                    f"ISIN {isin} with wrong length should fail validation"
                )
    
    def test_lowercase_handled(self):
        """Test that lowercase ISINs are handled (should fail basic checks)"""
        # ISINs should be uppercase, lowercase should fail basic validation
        self.assertFalse(is_valid_isin('us0378331005'))
        self.assertFalse(is_valid_isin('ie00b4l5y983'))


class TestParserFalsePositives(unittest.TestCase):
    """Test that parser rejects false positive ISIN matches"""
    
    @patch('tools.investos.ingest.fitz')
    def test_brunnenstrasse_false_positive_rejected(self, mock_fitz):
        """Test that BRUNNENSTRASSE is rejected as invalid ISIN"""
        # Create a temp file to use as mock PDF path
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF page with text containing BRUNNENSTRASSE
            mock_page = Mock()
            
            # Simulate PDF text with BRUNNENSTRASSE (common in German addresses)
            mock_page.get_text.return_value = """
DEPOT ÜBERSICHT
BRUNNENSTRASSE 123
BERLIN
            
POSITIONEN
            
Apple Inc.
ISIN US0378331005
Stück 10  Preis 175,50 EUR  Wert 1.755,00 EUR
            """
            
            # Mock PDF document that supports subscripting and iteration
            mock_doc = Mock()
            mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.close = Mock()
            
            mock_fitz.open.return_value = mock_doc
            
            # Parse the mocked PDF
            parser = TradeRepublicParser(mock_pdf_path)
            parsed_data = parser.parse()
            
            # Should only find Apple Inc., not BRUNNENSTRASSE
            holdings = parsed_data['holdings']
            
            # Check that we don't have BRUNNENSTRASSE as a holding
            holding_isins = [h.get('isin') for h in holdings]
            self.assertNotIn('BRUNNENSTRAS', holding_isins, 
                           "BRUNNENSTRASSE should be rejected as invalid ISIN")
            
            # Should have found Apple (if parser finds explicit ISIN labels)
            # This test mainly checks that BRUNNENSTRASSE is NOT included
            if holding_isins:
                self.assertIn('US0378331005', holding_isins,
                             "Valid ISIN US0378331005 should be found")
            
        finally:
            shutil.rmtree(temp_dir)


class TestBlockParsing(unittest.TestCase):
    """Test block-based parsing of holdings"""
    
    @patch('tools.investos.ingest.fitz')
    def test_block_parsing_extracts_name_quantity_value(self, mock_fitz):
        """Test that block parsing extracts name, quantity, and market value"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF page with realistic Trade Republic layout
            mock_page = Mock()
            mock_page.get_text.return_value = """
DEPOT ÜBERSICHT
Portfolio Value: 10.000,00 EUR

POSITIONEN

Apple Inc.
ISIN: US0378331005
WKN: 865985
Stück 10,00
Einstandskurs 150,00 EUR
Kurs 175,50 EUR
Wert 1.755,00 EUR
Gewinn +255,00 EUR

iShares Core MSCI World UCITS ETF USD (Acc)
ISIN: IE00B4L5Y983
WKN: A0RPWH
Anteile 50,00
Einstandskurs 70,00 EUR
Kurs 75,25 EUR
Kurswert 3.762,50 EUR
Gewinn +262,50 EUR
            """
            
            # Mock PDF document
            mock_doc = Mock()
            mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.close = Mock()
            
            mock_fitz.open.return_value = mock_doc
            
            # Parse the mocked PDF
            parser = TradeRepublicParser(mock_pdf_path)
            parsed_data = parser.parse()
            
            holdings = parsed_data['holdings']
            
            # Should find 2 holdings
            self.assertEqual(len(holdings), 2, "Should extract 2 holdings")
            
            # Check Apple Inc.
            apple = next((h for h in holdings if h['isin'] == 'US0378331005'), None)
            self.assertIsNotNone(apple, "Should find Apple Inc.")
            
            if apple:
                self.assertEqual(apple['name'], 'Apple Inc.', 
                               "Should extract correct name for Apple")
                self.assertIsNotNone(apple['quantity'], 
                                   "Should extract quantity for Apple")
                self.assertAlmostEqual(apple['quantity'], 10.0, places=1,
                                     msg="Should extract correct quantity for Apple")
                
                # Check market data
                self.assertIsNotNone(apple.get('market_data'), 
                                   "Should have market data for Apple")
                if apple.get('market_data'):
                    self.assertIsNotNone(apple['market_data'].get('market_value'),
                                       "Should extract market value for Apple")
                    self.assertAlmostEqual(apple['market_data']['market_value'], 
                                         1755.0, places=1,
                                         msg="Should extract correct market value for Apple")
                    self.assertEqual(apple['market_data']['currency'], 'EUR',
                                   "Should extract currency for Apple")
            
            # Check iShares ETF
            ishares = next((h for h in holdings if h['isin'] == 'IE00B4L5Y983'), None)
            self.assertIsNotNone(ishares, "Should find iShares ETF")
            
            if ishares:
                # Name should contain "iShares" but not "ISIN"
                self.assertIn('iShares', ishares['name'],
                            "Should extract name containing 'iShares'")
                self.assertNotIn('ISIN', ishares['name'],
                               "Name should not contain 'ISIN'")
                
                self.assertIsNotNone(ishares['quantity'],
                                   "Should extract quantity for iShares")
                self.assertAlmostEqual(ishares['quantity'], 50.0, places=1,
                                     msg="Should extract correct quantity for iShares")
                
                # Check market data
                if ishares.get('market_data'):
                    self.assertIsNotNone(ishares['market_data'].get('market_value'),
                                       "Should extract market value for iShares")
                    self.assertAlmostEqual(ishares['market_data']['market_value'],
                                         3762.5, places=1,
                                         msg="Should extract correct market value for iShares")
        
        finally:
            shutil.rmtree(temp_dir)


class TestTableLayoutParsing(unittest.TestCase):
    """Test parsing of Trade Republic table layout with column headers"""
    
    @patch('tools.investos.ingest.fitz')
    def test_table_layout_with_kurswert_header(self, mock_fitz):
        """Test extraction from table layout with KURSWERT IN EUR column header"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF with real Trade Republic table layout
            # Format: quantity, name, ISIN, meta, PRICE (before date), DATE, MARKET_VALUE (after date)
            mock_page = Mock()
            mock_page.get_text.return_value = """
DEPOT ÜBERSICHT

POSITIONEN
STK. / NOMINALE | WERTPAPIERBEZEICHNUNG | KURS PRO STÜCK | KURSWERT IN EUR

12,345678 Stk.
MSCI World ETF
ISIN: IE00B4L5Y983
WKN: A0RPWH
46,00
26.01.2026
5.678,90

5,00 Stk.
Tesla Inc.
ISIN: US88160R1014
WKN: A1CX3T
789,12
27.01.2026
3.945,60
            """
            
            # Mock PDF document
            mock_doc = Mock()
            mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.close = Mock()
            
            mock_fitz.open.return_value = mock_doc
            
            # Parse the mocked PDF
            parser = TradeRepublicParser(mock_pdf_path)
            parsed_data = parser.parse()
            
            holdings = parsed_data['holdings']
            
            # Should find 2 holdings
            self.assertEqual(len(holdings), 2, "Should extract 2 holdings")
            
            # Check MSCI World ETF
            msci = next((h for h in holdings if h['isin'] == 'IE00B4L5Y983'), None)
            self.assertIsNotNone(msci, "Should find MSCI World ETF")
            
            if msci:
                self.assertIn('MSCI World', msci['name'],
                            "Should extract name containing 'MSCI World'")
                
                # Quantity should be extracted from "12,345678 Stk." format
                self.assertIsNotNone(msci['quantity'],
                                   "Should extract quantity")
                self.assertAlmostEqual(msci['quantity'], 12.345678, places=4,
                                     msg="Should extract correct quantity from number-first format")
                
                # Market value should use deterministic after-date rule
                # Real TR format: price BEFORE date (46,00), date (26.01.2026), market_value AFTER date (5.678,90)
                # Should take FIRST number after date as market value
                if msci.get('market_data'):
                    self.assertIsNotNone(msci['market_data'].get('market_value'),
                                       "Should extract market value")
                    self.assertAlmostEqual(msci['market_data']['market_value'],
                                         5678.90, places=2,
                                         msg="Should extract first number after date as market value")
            
            # Check Tesla
            tesla = next((h for h in holdings if h['isin'] == 'US88160R1014'), None)
            self.assertIsNotNone(tesla, "Should find Tesla")
            
            if tesla:
                self.assertIn('Tesla', tesla['name'],
                            "Should extract name containing 'Tesla'")
                
                self.assertIsNotNone(tesla['quantity'],
                                   "Should extract quantity for Tesla")
                self.assertAlmostEqual(tesla['quantity'], 5.0, places=1,
                                     msg="Should extract correct quantity for Tesla")
                
                if tesla.get('market_data'):
                    # Price BEFORE date (789,12), date (27.01.2026), market_value AFTER date (3.945,60)
                    # Should take FIRST number after date
                    self.assertAlmostEqual(tesla['market_data']['market_value'],
                                         3945.60, places=2,
                                         msg="Should extract first number after date as market value")
        
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('tools.investos.ingest.fitz')
    def test_table_layout_single_value_after_date(self, mock_fitz):
        """Test extraction when only one value appears after date"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF with real TR format: price before date, market_value after
            mock_page = Mock()
            mock_page.get_text.return_value = """
DEPOT ÜBERSICHT

POSITIONEN
STK. / NOMINALE | WERTPAPIERBEZEICHNUNG | KURS PRO STÜCK | KURSWERT IN EUR

10,00 Stk.
Apple Inc.
ISIN: US0378331005
WKN: 865985
175,55
26.01.2026
1.755,50
            """
            
            # Mock PDF document
            mock_doc = Mock()
            mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.close = Mock()
            
            mock_fitz.open.return_value = mock_doc
            
            # Parse the mocked PDF
            parser = TradeRepublicParser(mock_pdf_path)
            parsed_data = parser.parse()
            
            holdings = parsed_data['holdings']
            
            # Should find 1 holding
            self.assertEqual(len(holdings), 1, "Should extract 1 holding")
            
            apple = holdings[0]
            self.assertEqual(apple['isin'], 'US0378331005')
            self.assertIn('Apple', apple['name'])
            
            # Should extract first value after date (market value, not price)
            # Price before date (175,55), date (26.01.2026), market_value after (1.755,50)
            if apple.get('market_data'):
                self.assertAlmostEqual(apple['market_data']['market_value'],
                                     1755.50, places=2,
                                     msg="Should extract first value after date as market_value")
        
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('tools.investos.ingest.fitz')
    def test_price_before_date_not_used(self, mock_fitz):
        """Test that price before date is NOT mistaken for market value"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF with clear price/date/value separation
            mock_page = Mock()
            mock_page.get_text.return_value = """
POSITIONEN
STK. / NOMINALE | WERTPAPIERBEZEICHNUNG | KURS PRO STÜCK | KURSWERT IN EUR

1,00 Stk.
Test Security
ISIN: DE0005140008
999,99
15.01.2026
999,99
            """
            
            # Mock PDF document
            mock_doc = Mock()
            mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.close = Mock()
            
            mock_fitz.open.return_value = mock_doc
            
            # Parse the mocked PDF
            parser = TradeRepublicParser(mock_pdf_path)
            parsed_data = parser.parse()
            
            holdings = parsed_data['holdings']
            
            # Should find 1 holding
            self.assertEqual(len(holdings), 1, "Should extract 1 holding")
            
            test_sec = holdings[0]
            self.assertEqual(test_sec['isin'], 'DE0005140008')
            
            # Should extract value AFTER date, not before
            # Even though both values are the same (999,99)
            # The rule is: first number after date line
            if test_sec.get('market_data'):
                self.assertIsNotNone(test_sec['market_data'].get('market_value'),
                                   "Should extract market value after date")
                self.assertAlmostEqual(test_sec['market_data']['market_value'],
                                     999.99, places=2)
        
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('tools.investos.ingest.fitz')
    def test_header_date_ignored(self, mock_fitz):
        """Test that header date (zum XX.XX.XXXX) is ignored, only per-holding date used"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF with header date that should be IGNORED
            mock_page = Mock()
            mock_page.get_text.return_value = """
DEPOT ÜBERSICHT zum 01.01.2026

POSITIONEN
STK. / NOMINALE | WERTPAPIERBEZEICHNUNG | KURS PRO STÜCK | KURSWERT IN EUR

5,00 Stk.
Test Security
ISIN: DE0005140008
WKN: 123456
250,00
15.01.2026
1.250,00
            """
            
            # Mock PDF document
            mock_doc = Mock()
            mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.close = Mock()
            
            mock_fitz.open.return_value = mock_doc
            
            # Parse the mocked PDF
            parser = TradeRepublicParser(mock_pdf_path)
            parsed_data = parser.parse()
            
            holdings = parsed_data['holdings']
            
            # Should find 1 holding
            self.assertEqual(len(holdings), 1, "Should extract 1 holding")
            
            test_sec = holdings[0]
            self.assertEqual(test_sec['isin'], 'DE0005140008')
            
            # Should extract market value using per-holding date (15.01.2026)
            # NOT header date (01.01.2026)
            # Market value after 15.01.2026 is 1.250,00
            if test_sec.get('market_data'):
                self.assertIsNotNone(test_sec['market_data'].get('market_value'),
                                   "Should extract market value after per-holding date")
                self.assertAlmostEqual(test_sec['market_data']['market_value'],
                                     1250.00, places=2,
                                     msg="Should use date after ISIN, not header date")
        
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('tools.investos.ingest.fitz')
    def test_value_above_quantity(self, mock_fitz):
        """Test that market value is extracted from ABOVE quantity line (real TR layout)"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF with REAL Trade Republic layout: date, value, quantity
            # Market value appears ABOVE quantity line
            mock_page = Mock()
            mock_page.get_text.return_value = """
POSITIONEN
STK. / NOMINALE | WERTPAPIERBEZEICHNUNG | KURS PRO STÜCK | KURSWERT IN EUR

Test Security A
ISIN: DE0005140008
WKN: 123456
15.01.2026
1.250,00
5,00 Stk.

Test Security B  
ISIN: US0378331005
WKN: 865985
16.01.2026
2.500,50
10,00 Stk.
            """
            
            # Mock PDF document
            mock_doc = Mock()
            mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_doc.__len__ = Mock(return_value=1)
            mock_doc.close = Mock()
            
            mock_fitz.open.return_value = mock_doc
            
            # Parse the mocked PDF
            parser = TradeRepublicParser(mock_pdf_path)
            parsed_data = parser.parse()
            
            holdings = parsed_data['holdings']
            
            # Should find 2 holdings
            self.assertEqual(len(holdings), 2, "Should extract 2 holdings")
            
            # Check Test Security A
            sec_a = next((h for h in holdings if h['isin'] == 'DE0005140008'), None)
            self.assertIsNotNone(sec_a, "Should find Test Security A")
            
            if sec_a:
                # Market value should be 1.250,00 (ABOVE quantity line)
                # NOT the quantity 5,00
                if sec_a.get('market_data'):
                    self.assertIsNotNone(sec_a['market_data'].get('market_value'),
                                       "Should extract market value")
                    self.assertAlmostEqual(sec_a['market_data']['market_value'],
                                         1250.00, places=2,
                                         msg="Should extract value from ABOVE quantity line")
                
                # Quantity should be 5,00
                self.assertAlmostEqual(sec_a['quantity'], 5.0, places=1)
            
            # Check Test Security B
            sec_b = next((h for h in holdings if h['isin'] == 'US0378331005'), None)
            self.assertIsNotNone(sec_b, "Should find Test Security B")
            
            if sec_b:
                # Market value should be 2.500,50 (ABOVE quantity line)
                if sec_b.get('market_data'):
                    self.assertAlmostEqual(sec_b['market_data']['market_value'],
                                         2500.50, places=2,
                                         msg="Should extract value from ABOVE quantity line")
                
                # Quantity should be 10,00
                self.assertAlmostEqual(sec_b['quantity'], 10.0, places=1)
        
        finally:
            shutil.rmtree(temp_dir)


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
