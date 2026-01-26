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


class TestColumnBasedParsing(unittest.TestCase):
    """Test column-based parsing architecture (NEW)"""
    
    @patch('tools.investos.ingest.fitz')
    def test_first_row_isin_below_quantity_allowed(self, mock_fitz):
        """
        MANDATORY TEST: First-row ISIN below quantity exception (bounded).
        
        Tests the bounded exception that allows ISIN lookup BELOW quantity
        for the FIRST holding only, to handle PDF text extraction ordering.
        """
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF where FIRST holding has ISIN below quantity (PDF artifact)
            # SECOND holding has ISIN above (normal case)
            mock_page = Mock()
            mock_page.get_text.return_value = """
DEPOT ÜBERSICHT

POSITIONEN
STK. / NOMINALE | WERTPAPIERBEZEICHNUNG | KURS PRO STÜCK | KURSWERT IN EUR

14,007714 Stk.
Fairfax Financial Holdings Ltd.
Registered Shares (Sub. Vtg) o.N.
ISIN: CA3039011026
1.398,00
19.582,78
474,155346 Stk.
TORM PLC
Registered Shares A DL -,01
ISIN: GB00BZ3CNK81
26.01.2026
9.030,29
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
            warnings = parsed_data['warnings']
            metadata = parsed_data.get('metadata', {})
            
            # Should extract 2 holdings (not reject first one)
            self.assertEqual(len(holdings), 2, "Should extract both holdings")
            
            # Check first holding (ISIN below quantity)
            first = next((h for h in holdings if h['isin'] == 'CA3039011026'), None)
            self.assertIsNotNone(first, "First holding should be extracted with ISIN below quantity")
            if first:
                self.assertIn('Fairfax', first['name'], "Should extract correct name")
                self.assertAlmostEqual(first['quantity'], 14.007714, places=4)
            
            # Check second holding (ISIN above quantity - normal case)
            second = next((h for h in holdings if h['isin'] == 'GB00BZ3CNK81'), None)
            self.assertIsNotNone(second, "Second holding should be extracted normally")
            if second:
                self.assertIn('TORM', second['name'], "Should extract correct name")
                self.assertAlmostEqual(second['quantity'], 474.155346, places=4)
            
            # Verify warning was emitted
            self.assertTrue(
                any('ISIN found below quantity for first holding' in w for w in warnings),
                "Warning should be emitted for first-row exception"
            )
            
            # Verify exactly ONE warning for this exception
            exception_warnings = [w for w in warnings if 'ISIN found below quantity' in w]
            self.assertEqual(len(exception_warnings), 1,
                           "Should have exactly ONE warning for first-row exception")
            
            # Verify metadata note
            notes = metadata.get('notes', [])
            self.assertTrue(
                any('First holding ISIN resolved below quantity' in note for note in notes),
                "Metadata should include note about first-row exception"
            )
            
            # CRITICAL: Verify second holding does NOT reuse first ISIN
            if first and second:
                self.assertNotEqual(first['isin'], second['isin'],
                                  "Second holding must have different ISIN")
        
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('tools.investos.ingest.fitz')
    def test_column_detection(self, mock_fitz):
        """Test that column headers are correctly detected"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF with column headers
            mock_page = Mock()
            mock_page.get_text.return_value = """
DEPOT ÜBERSICHT

POSITIONEN
STK. / NOMINALE | WERTPAPIERBEZEICHNUNG | KURS PRO STÜCK | KURSWERT IN EUR

Test Content
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
            lines = parser.extract_text_lines()
            columns = parser.detect_columns(lines)
            
            # Should detect all 4 columns
            self.assertIn('quantity', columns, "Should detect quantity column")
            self.assertIn('name', columns, "Should detect name column")
            self.assertIn('price', columns, "Should detect price column")
            self.assertIn('market_value', columns, "Should detect market_value column")
            self.assertIn('currency', columns, "Should extract currency from header")
            self.assertEqual(columns['currency'], 'EUR')
            
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('tools.investos.ingest.fitz')
    def test_quantity_line_identification(self, mock_fitz):
        """Test that quantity lines are correctly identified"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF with multiple quantity lines
            mock_page = Mock()
            mock_page.get_text.return_value = """
POSITIONEN
STK. / NOMINALE | WERTPAPIERBEZEICHNUNG | KURS PRO STÜCK | KURSWERT IN EUR

5,00 Stk.
Test Security A
ISIN: DE0005140008

10,5 Stk.
Test Security B
ISIN: US0378331005

100,123 Stk.
Test Security C
ISIN: IE00B4L5Y983
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
            lines = parser.extract_text_lines()
            quantity_lines = parser.find_quantity_lines(lines)
            
            # Should find 3 quantity lines
            self.assertEqual(len(quantity_lines), 3, "Should find all 3 quantity lines")
            
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('tools.investos.ingest.fitz')
    def test_market_value_column_alignment_critical(self, mock_fitz):
        """
        CRITICAL TEST: Market value must come from KURSWERT column, NOT proximity.
        This test MUST FAIL if proximity/heuristic logic is used.
        """
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF where column-based extraction is REQUIRED
            # Trade Republic format: Quantity -> Name -> ISIN -> Price -> Date -> Market Value
            # Market value 1.234,56 should be extracted (not price 125,50)
            mock_page = Mock()
            mock_page.get_text.return_value = """
DEPOT ÜBERSICHT

POSITIONEN
STK. / NOMINALE | WERTPAPIERBEZEICHNUNG | KURS PRO STÜCK | KURSWERT IN EUR

3,00 Stk.
Test Security
ISIN: DE0005140008
WKN: 123456
125,50
26.01.2026
1.234,56
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
            self.assertAlmostEqual(test_sec['quantity'], 3.0, places=1,
                                 msg="Should extract quantity from quantity line")
            
            # CRITICAL: Market value must be 1.234,56 from KURSWERT column
            # NOT 3,00 from proximity to quantity line
            if test_sec.get('market_data'):
                self.assertAlmostEqual(test_sec['market_data']['market_value'],
                                     1234.56, places=2,
                                     msg="CRITICAL: Market value must come from KURSWERT column, not proximity to quantity")
        
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('tools.investos.ingest.fitz')
    def test_isin_belongs_to_row_below(self, mock_fitz):
        """Test that each ISIN is assigned to correct quantity line below it"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF with multiple ISINs (Trade Republic format: Qty -> Name -> ISIN)
            mock_page = Mock()
            mock_page.get_text.return_value = """
POSITIONEN
STK. / NOMINALE | WERTPAPIERBEZEICHNUNG | KURS PRO STÜCK | KURSWERT IN EUR

5,00 Stk.
Security A
ISIN: DE0005140008
26.01.2026
1.000,00

10,00 Stk.
Security B
ISIN: US0378331005
26.01.2026
2.000,00

15,00 Stk.
Security C
ISIN: IE00B4L5Y983
26.01.2026
3.000,00
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
            
            # Should find 3 holdings
            self.assertEqual(len(holdings), 3, "Should extract 3 holdings")
            
            # Check each ISIN assigned correctly
            sec_a = next((h for h in holdings if h['isin'] == 'DE0005140008'), None)
            self.assertIsNotNone(sec_a)
            if sec_a:
                self.assertAlmostEqual(sec_a['quantity'], 5.0, places=1)
            
            sec_b = next((h for h in holdings if h['isin'] == 'US0378331005'), None)
            self.assertIsNotNone(sec_b)
            if sec_b:
                self.assertAlmostEqual(sec_b['quantity'], 10.0, places=1)
            
            sec_c = next((h for h in holdings if h['isin'] == 'IE00B4L5Y983'), None)
            self.assertIsNotNone(sec_c)
            if sec_c:
                self.assertAlmostEqual(sec_c['quantity'], 15.0, places=1)
        
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('tools.investos.ingest.fitz')
    def test_name_stops_at_boundaries(self, mock_fitz):
        """Test name extraction stops at: ISIN, headers, previous quantity"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF with multi-line name (Trade Republic format: Qty -> Name -> ISIN)
            mock_page = Mock()
            mock_page.get_text.return_value = """
POSITIONEN
STK. / NOMINALE | WERTPAPIERBEZEICHNUNG | KURS PRO STÜCK | KURSWERT IN EUR

5,00 Stk.
Multi Line
Security Name
Test Corp
ISIN: DE0005140008
26.01.2026
1.000,00
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
            
            self.assertEqual(len(holdings), 1)
            
            # Name should be multi-line but stop at ISIN
            name = holdings[0]['name']
            self.assertIn('Test Corp', name, "Should include name lines")
            self.assertNotIn('ISIN', name, "Should not include ISIN in name")
        
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('tools.investos.ingest.fitz')
    def test_missing_column_header_produces_warning(self, mock_fitz):
        """Test that missing KURSWERT column produces warning and null market_value"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF WITHOUT KURSWERT header (Trade Republic format: Qty -> Name -> ISIN)
            mock_page = Mock()
            mock_page.get_text.return_value = """
DEPOT ÜBERSICHT

POSITIONEN

5,00 Stk.
Test Security
ISIN: DE0005140008
1.234,56
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
            
            # Should have warning
            self.assertTrue(len(parsed_data['warnings']) > 0, 
                          "Should produce warning when column header missing")
            self.assertTrue(any('KURSWERT' in w for w in parsed_data['warnings']),
                          "Warning should mention missing KURSWERT column")
            
            # Market value should be None
            holdings = parsed_data['holdings']
            if len(holdings) > 0:
                test_sec = holdings[0]
                self.assertIsNone(test_sec.get('market_data'),
                                "Market data should be None when column not detected")
        
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('tools.investos.ingest.fitz')
    def test_brunnenstrasse_false_positive_rejected(self, mock_fitz):
        """Test that BRUNNENSTRASSE is rejected as invalid ISIN"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            mock_pdf_path = temp_dir / 'test.pdf'
            mock_pdf_path.touch()
            
            # Mock PDF with BRUNNENSTRASSE (common German street name)
            # Trade Republic format: Qty -> Name -> ISIN
            mock_page = Mock()
            mock_page.get_text.return_value = """
DEPOT ÜBERSICHT
BRUNNENSTRASSE 123
BERLIN

POSITIONEN
STK. / NOMINALE | WERTPAPIERBEZEICHNUNG | KURS PRO STÜCK | KURSWERT IN EUR

10,00 Stk.
Apple Inc.
ISIN: US0378331005
26.01.2026
1.755,00
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
            holding_isins = [h.get('isin') for h in holdings]
            
            # Should NOT have BRUNNENSTRASSE
            self.assertNotIn('BRUNNENSTRAS', holding_isins,
                           "BRUNNENSTRASSE should be rejected by ISIN validation")
            
            # Should have Apple
            self.assertIn('US0378331005', holding_isins,
                        "Valid ISIN should be found")
        
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
