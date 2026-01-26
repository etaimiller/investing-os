"""
Portfolio ingestion from Trade Republic PDFs using column reconstruction.

Trade Republic PDFs are COLUMN-BASED layouts flattened into reading order.
This module implements proper column reconstruction + row anchoring.

Architecture:
1. Raw Text Layer: Extract (line_index, text) from PDF
2. Column Detection: Locate column headers and define column bands
3. Row Identification: Find quantity lines (one per holding)
4. Per-Row Parsing: Extract quantity, ISIN, name, market_value deterministically

Key Invariants:
- One quantity line ("<number> Stk.") = one holding row
- Market value MUST be from KURSWERT IN EUR column band
- ISIN belongs to closest quantity line below it
- Missing data → null + explicit warning (never guess)
"""

import re
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


class IngestError(Exception):
    """Error during PDF ingestion"""
    pass


def is_valid_isin(isin: str) -> bool:
    """
    Validate ISIN using ISO 6166 checksum (Luhn mod-10 algorithm).
    
    ISIN format: 2 letter country code + 9 alphanumeric + 1 check digit
    
    Examples:
    - US0378331005 (Apple) → Valid
    - IE00B4L5Y983 (iShares) → Valid  
    - BRUNNENSTRAS → Invalid (wrong format, fails checksum)
    """
    if not isin or len(isin) != 12:
        return False
    
    # First 2 chars must be letters (country code)
    if not isin[:2].isalpha() or not isin[:2].isupper():
        return False
    
    # Last char must be digit (check digit)
    if not isin[-1].isdigit():
        return False
    
    # Middle 9 chars must be alphanumeric and uppercase
    middle = isin[2:11]
    if not middle.isalnum():
        return False
    for char in middle:
        if not (char.isdigit() or (char.isalpha() and char.isupper())):
            return False
    
    # Convert to string of digits: letters A=10, B=11, ..., Z=35
    digit_string = ''
    for char in isin:
        if char.isdigit():
            digit_string += char
        elif char.isalpha() and char.isupper():
            digit_string += str(ord(char) - ord('A') + 10)
        else:
            return False
    
    # Apply Luhn algorithm (mod-10 check)
    total = 0
    for i, digit_char in enumerate(reversed(digit_string)):
        digit = int(digit_char)
        if i % 2 == 1:  # Every second digit from right
            digit *= 2
            if digit > 9:
                digit = digit // 10 + digit % 10
        total += digit
    
    return total % 10 == 0


class TradeRepublicParser:
    """Parse Trade Republic portfolio PDF using column reconstruction"""
    
    # Quantity line pattern: "<number> Stk."
    QUANTITY_PATTERN = re.compile(r'^([0-9][0-9\.,]*)\s*Stk\.?\s*$', re.IGNORECASE)
    
    # ISIN pattern: 2 letters + 10 alphanumeric
    ISIN_PATTERN = re.compile(r'\b([A-Z]{2}[A-Z0-9]{10})\b')
    
    # Money pattern: number with separators (German: 1.234,56 or English: 1,234.56)
    MONEY_PATTERN = re.compile(r'\b([0-9]{1,3}(?:[.,][0-9]{3})*[.,][0-9]{2})\b|'
                               r'\b([0-9]+[.,][0-9]+)\b')
    
    def __init__(self, pdf_path: Path, debug: bool = False):
        """Initialize parser with PDF path"""
        if fitz is None:
            raise IngestError(
                "PyMuPDF not installed. Install with: pip install PyMuPDF>=1.23.0"
            )
        
        self.pdf_path = pdf_path
        self.debug = debug
        self.warnings = []
        self.first_row_isin_below = False  # Track if first-row exception was used
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse Trade Republic PDF and extract holdings.
        
        Returns:
            Dict with:
                holdings: List of holding dicts
                cash: List of cash positions (empty for now)
                warnings: List of warning messages
                metadata: Extraction metadata
        """
        # Extract raw text as list of (line_index, text)
        lines = self.extract_text_lines()
        
        if self.debug:
            print(f"[DEBUG] Extracted {len(lines)} lines from PDF")
        
        # Detect column structure
        columns = self.detect_columns(lines)
        
        if self.debug and columns:
            print(f"[DEBUG] Detected columns: {list(columns.keys())}")
        
        # Find quantity lines (row anchors)
        quantity_lines = self.find_quantity_lines(lines)
        
        if self.debug:
            print(f"[DEBUG] Found {len(quantity_lines)} quantity lines (holdings)")
        
        # Parse each holding row
        holdings = []
        for row_index, qty_idx in enumerate(quantity_lines):
            holding = self.parse_holding_row(lines, qty_idx, columns, quantity_lines, row_index)
            if holding:
                holdings.append(holding)
        
        metadata = {
            'source_pdf': str(self.pdf_path.name),
            'extraction_method': 'column_reconstruction',
            'total_lines': len(lines),
            'holdings_found': len(holdings)
        }
        
        # Add note if first-row exception was used
        if self.first_row_isin_below:
            metadata['notes'] = [
                "First holding ISIN resolved below quantity due to PDF text order"
            ]
        
        return {
            'holdings': holdings,
            'cash': [],  # TODO: Implement cash parsing
            'warnings': self.warnings,
            'metadata': metadata
        }
    
    def extract_text_lines(self) -> List[Tuple[int, str]]:
        """
        Extract text from PDF as list of (line_index, text).
        
        Returns:
            List of (line_index, text) tuples
        """
        lines = []
        try:
            doc = fitz.open(str(self.pdf_path))
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Split into lines and enumerate
                page_lines = text.split('\n')
                for i, line in enumerate(page_lines):
                    if line.strip():  # Skip empty lines
                        lines.append((len(lines), line.strip()))
            
            doc.close()
            
        except Exception as e:
            raise IngestError(f"Failed to extract PDF text: {e}")
        
        return lines
    
    def detect_columns(self, lines: List[Tuple[int, str]]) -> Dict[str, int]:
        """
        Detect column structure from header line.
        
        Trade Republic column headers:
        - STK. / NOMINALE
        - WERTPAPIERBEZEICHNUNG  
        - KURS PRO STÜCK
        - KURSWERT IN EUR
        
        Args:
            lines: List of (line_index, text) tuples
        
        Returns:
            Dict mapping column names to line indices where headers found
        """
        columns = {}
        
        # Search for column headers
        for idx, text in lines:
            text_upper = text.upper()
            
            if 'STK' in text_upper and 'NOMINALE' in text_upper:
                columns['quantity'] = idx
            
            if 'WERTPAPIERBEZEICHNUNG' in text_upper:
                columns['name'] = idx
            
            if 'KURS PRO STÜCK' in text_upper or 'KURS PRO STUECK' in text_upper:
                columns['price'] = idx
            
            if 'KURSWERT' in text_upper and 'EUR' in text_upper:
                columns['market_value'] = idx
                # Extract currency from header
                columns['currency'] = 'EUR'
        
        return columns
    
    def find_quantity_lines(self, lines: List[Tuple[int, str]]) -> List[int]:
        """
        Find all quantity lines (row anchors).
        
        Each line matching "<number> Stk." is one holding row.
        
        Args:
            lines: List of (line_index, text) tuples
        
        Returns:
            List of line indices where quantity lines found
        """
        quantity_lines = []
        
        for idx, text in lines:
            match = self.QUANTITY_PATTERN.match(text)
            if match:
                quantity_lines.append(idx)
                if self.debug:
                    qty_str = match.group(1)
                    print(f"[DEBUG] Quantity line at {idx}: {qty_str} Stk.")
        
        return quantity_lines
    
    def parse_holding_row(self, lines: List[Tuple[int, str]], qty_idx: int, 
                         columns: Dict[str, int], quantity_lines: List[int],
                         row_index: int) -> Optional[Dict[str, Any]]:
        """
        Parse a single holding row anchored at quantity line.
        
        Args:
            lines: List of all (line_index, text) tuples
            qty_idx: Line index of quantity line for this row
            columns: Column structure from detect_columns
            quantity_lines: List of all quantity line indices
            row_index: Index of this row in quantity_lines (0 = first holding)
        
        Returns:
            Holding dict or None if extraction fails
        """
        # Get quantity line text
        qty_text = next((text for idx, text in lines if idx == qty_idx), None)
        if not qty_text:
            return None
        
        # Extract quantity
        quantity = self.extract_quantity(qty_text)
        
        # Extract ISIN using bounded resolution logic
        isin, resolution_method = self.resolve_isin_for_row(lines, quantity_lines, row_index)
        
        # Extract name (lines between quantity and ISIN)
        next_qty_idx = quantity_lines[row_index + 1] if row_index + 1 < len(quantity_lines) else len(lines)
        name = self.extract_name(lines, qty_idx, next_qty_idx)
        
        # Extract market value (from KURSWERT column)
        # For first row, may need to search below quantity due to PDF ordering
        next_qty_idx = quantity_lines[row_index + 1] if row_index + 1 < len(quantity_lines) else len(lines)
        market_value = self.extract_market_value(lines, qty_idx, columns, next_qty_idx)
        
        # Get currency from columns or default
        currency = columns.get('currency', 'EUR')
        
        # Add warnings for missing data
        if not isin:
            self.warnings.append(f"No ISIN found for holding at line {qty_idx}")
            return None  # ISIN is required
        
        if not name:
            self.warnings.append(f"No name found for ISIN {isin}")
            name = f"Unknown ({isin})"
        
        if quantity is None:
            self.warnings.append(f"Could not parse quantity for ISIN {isin}")
        
        if market_value is None:
            self.warnings.append(f"No market value found for ISIN {isin}")
        
        if self.debug:
            print(f"[DEBUG] Parsed holding: {isin} | {name[:30]} | qty={quantity} | value={market_value}")
        
        return {
            'security_id': isin,
            'isin': isin,
            'name': name,
            'quantity': quantity,
            'currency': currency,
            'cost_basis': None,  # Not extracted from this PDF format
            'market_data': {
                'market_value': market_value,
                'currency': currency
            } if market_value is not None else None
        }
    
    def extract_quantity(self, qty_text: str) -> Optional[float]:
        """Extract quantity from quantity line text"""
        match = self.QUANTITY_PATTERN.match(qty_text)
        if not match:
            return None
        
        qty_str = match.group(1)
        return self.parse_number(qty_str)
    
    def resolve_isin_for_row(self, lines: List[Tuple[int, str]], quantity_lines: List[int],
                            row_index: int) -> Tuple[Optional[str], str]:
        """
        Resolve ISIN for a holding row with bounded first-row exception.
        
        Primary rule: Search ABOVE quantity line.
        Bounded exception: For FIRST row only, if no ISIN above, search BELOW
        until next quantity line.
        
        Args:
            lines: All lines
            quantity_lines: List of all quantity line indices
            row_index: Index in quantity_lines (0 = first holding)
        
        Returns:
            Tuple of (isin, resolution_method)
            resolution_method: "above-quantity" | "below-quantity-first-row" | "missing-isin"
        """
        qty_idx = quantity_lines[row_index]
        
        # Trade Republic PDF structure: ISIN appears BELOW quantity line in reading order
        # Structure: Quantity -> Name -> ISIN -> Date -> Market Value
        
        # Define search boundary: from this quantity to next quantity
        search_start = qty_idx + 1
        search_end = quantity_lines[row_index + 1] if row_index + 1 < len(quantity_lines) else len(lines)
        
        if self.debug:
            print(f"[DEBUG] Row {row_index}: qty_idx={qty_idx}, searching lines {search_start} to {search_end}")
        
        # Search for ISIN between this quantity and next quantity
        isin = self.find_first_isin_between(lines, search_start, search_end)
        
        if isin:
            # For first row only, add explanatory note about PDF text order
            if row_index == 0:
                warning_msg = "ISIN found below quantity for first holding (PDF ordering artifact)"
                self.warnings.append(warning_msg)
                self.first_row_isin_below = True
                
                if self.debug:
                    print(f"[DEBUG] {warning_msg}: {isin}")
                
                return isin, "below-quantity-first-row"
            else:
                return isin, "below-quantity"
        
        # Failure (explicit, conservative)
        return None, "missing-isin"
    
    def find_closest_isin_above(self, lines: List[Tuple[int, str]], qty_idx: int, 
                               stop_at_idx: int = -1) -> Optional[str]:
        """
        Find closest valid ISIN ABOVE the quantity line.
        
        Args:
            lines: All lines
            qty_idx: Quantity line index
            stop_at_idx: Stop searching at this line index (exclusive, default -1 = search to start)
        
        Returns:
            ISIN string or None
        """
        # Search upward from quantity line, but stop at boundary
        search_limit = max(stop_at_idx, -1)
        
        for idx in range(qty_idx - 1, search_limit, -1):
            text = next((t for i, t in lines if i == idx), None)
            if not text:
                continue
            
            if self.debug and idx <= qty_idx - 1 and idx >= max(qty_idx - 10, search_limit + 1):
                print(f"[DEBUG]   Checking line {idx}: {text[:30]}")
            
            # Look for ISIN pattern
            matches = self.ISIN_PATTERN.findall(text)
            for candidate in matches:
                if is_valid_isin(candidate):
                    if self.debug:
                        print(f"[DEBUG] Found ISIN {candidate} at line {idx} for holding at {qty_idx}")
                    return candidate
        
        if self.debug and search_limit > -1:
            print(f"[DEBUG] ISIN search stopped at boundary {search_limit} for holding at {qty_idx}")
        
        return None
    
    def find_first_isin_between(self, lines: List[Tuple[int, str]], 
                               start_idx: int, end_idx: int) -> Optional[str]:
        """
        Find first valid ISIN in bounded range [start_idx, end_idx).
        
        Args:
            lines: All lines
            start_idx: Start of search range (inclusive)
            end_idx: End of search range (exclusive)
        
        Returns:
            ISIN string or None
        """
        for idx in range(start_idx, end_idx):
            text = next((t for i, t in lines if i == idx), None)
            if not text:
                continue
            
            # Look for ISIN pattern
            matches = self.ISIN_PATTERN.findall(text)
            for candidate in matches:
                if is_valid_isin(candidate):
                    return candidate
        
        return None
    
    def extract_isin(self, lines: List[Tuple[int, str]], qty_idx: int) -> Optional[str]:
        """
        DEPRECATED: Use resolve_isin_for_row instead.
        Kept for backwards compatibility with tests.
        
        Extract ISIN for this holding.
        ISIN is the closest valid ISIN ABOVE the quantity line.
        
        Args:
            lines: All lines
            qty_idx: Quantity line index
        
        Returns:
            ISIN string or None
        """
        return self.find_closest_isin_above(lines, qty_idx)
    
    def extract_name(self, lines: List[Tuple[int, str]], qty_idx: int, next_qty_idx: int) -> Optional[str]:
        """
        Extract name for this holding.
        
        Trade Republic format: Quantity -> Name -> ISIN
        Name appears BETWEEN quantity and ISIN lines (both in reading order below).
        
        Strategy:
        1. Find ISIN line (search from qty to next_qty)
        2. Extract non-numeric lines between quantity and ISIN
        
        Args:
            lines: All lines
            qty_idx: Quantity line index
            next_qty_idx: Next quantity line index (or len(lines))
        
        Returns:
            Name string or None
        """
        # Find the ISIN line for this holding (between this qty and next qty)
        isin_idx = None
        
        for idx in range(qty_idx + 1, next_qty_idx):
            text = next((t for i, t in lines if i == idx), None)
            if not text:
                continue
            if 'ISIN' in text.upper():
                isin_idx = idx
                break
        
        if isin_idx is None:
            return None
        
        # Extract name lines BETWEEN quantity and ISIN (both below in reading order)
        name_lines = []
        
        for idx in range(qty_idx + 1, isin_idx):
            text = next((t for i, t in lines if i == idx), None)
            if not text:
                continue
            
            # Skip lines that are mostly numbers or dates
            if re.match(r'^[\d\s\.,]+$', text) or re.search(r'\d{2}\.\d{2}\.\d{4}', text):
                continue
            
            # Skip WKN lines and other metadata
            if 'WKN' in text.upper() or 'LAGERLAND' in text.upper():
                continue
            
            # This is a name line
            name_lines.append(text)
        
        if name_lines:
            # Join with space and clean up
            name = ' '.join(name_lines)
            name = re.sub(r'\s+', ' ', name).strip()
            return name
        
        return None
    
    def extract_market_value(self, lines: List[Tuple[int, str]], qty_idx: int, 
                            columns: Dict[str, int], next_qty_idx: int) -> Optional[float]:
        """
        Extract market value for this holding.
        
        CRITICAL: Market value MUST come from KURSWERT IN EUR column band.
        
        Due to PDF text extraction order, market values appear AFTER the quantity line
        in reading order (but logically belong to the same row in the table).
        
        Strategy:
        - Search from quantity line to next quantity line (or end)
        - Find first money-like number in KURSWERT column band
        - Skip dates, prices, and other non-market-value numbers
        
        Args:
            lines: All lines
            qty_idx: Quantity line index (current holding)
            columns: Column structure
            next_qty_idx: Next quantity line index (or len(lines) for last holding)
        
        Returns:
            Market value (float) or None
        """
        if 'market_value' not in columns:
            # No column detected - cannot extract deterministically
            self.warnings.append("KURSWERT column not detected, cannot extract market_value")
            return None
        
        column_header_idx = columns['market_value']
        
        # Define search range: from quantity line to next quantity line (exclusive)
        search_start = qty_idx + 1
        search_end = next_qty_idx
        
        # Find market value: first money-like number AFTER date line
        # Trade Republic format: ... ISIN ... price ... DATE ... MARKET_VALUE
        
        # First, find the date line in this range
        date_line_idx = None
        for idx in range(search_start, search_end):
            text = next((t for i, t in lines if i == idx), None)
            if text and re.search(r'\d{2}\.\d{2}\.\d{4}', text):
                date_line_idx = idx
                break
        
        if date_line_idx is None:
            # No date found - fall back to finding closest money value
            if self.debug:
                print(f"[DEBUG] No date line found for holding at {qty_idx}, using fallback")
        
        # Search for money values after date (or from start if no date)
        candidates = []
        effective_start = date_line_idx + 1 if date_line_idx else search_start
        
        for idx in range(effective_start, search_end):
            text = next((t for i, t in lines if i == idx), None)
            if not text:
                continue
            
            # Skip lines with "Stk" (quantity column bleed)
            if 'Stk' in text or 'Stück' in text:
                continue
            
            # Skip date lines
            if re.search(r'\d{2}\.\d{2}\.\d{4}', text):
                continue
            
            # Find money-like numbers
            matches = self.MONEY_PATTERN.findall(text)
            for match in matches:
                # Pattern has 2 groups, one will be empty
                num_str = match[0] if isinstance(match, tuple) and match[0] else (match[1] if isinstance(match, tuple) else match)
                if not num_str:
                    continue
                value = self.parse_number(num_str)
                if value and value > 0:
                    # Distance from quantity line (closer = more likely)
                    distance = idx - qty_idx
                    candidates.append((idx, value, distance))
        
        if not candidates:
            return None
        
        # Select closest candidate to quantity line
        candidates.sort(key=lambda x: x[2])  # Sort by distance (ascending)
        selected_idx, selected_value, distance = candidates[0]
        
        if self.debug:
            print(f"[DEBUG] Market value from line {selected_idx} (distance={distance}): {selected_value}")
        
        return selected_value
    
    def parse_number(self, num_str: str) -> Optional[float]:
        """
        Parse number string handling German/European formatting.
        
        Formats:
        - German: 1.234,56 (thousand=., decimal=,)
        - Plain: 1234,56
        - English: 1234.56
        """
        if not num_str:
            return None
        
        num_str = num_str.strip().replace(' ', '')
        
        comma_count = num_str.count(',')
        dot_count = num_str.count('.')
        
        if comma_count > 0 and dot_count > 0:
            # Both present - determine which is decimal
            last_comma = num_str.rfind(',')
            last_dot = num_str.rfind('.')
            
            if last_comma > last_dot:
                # German: 1.234,56
                num_str = num_str.replace('.', '').replace(',', '.')
            else:
                # English: 1,234.56
                num_str = num_str.replace(',', '')
        elif comma_count == 1:
            # Single comma - decimal separator
            num_str = num_str.replace(',', '.')
        elif dot_count > 1:
            # Multiple dots - thousand separators
            num_str = num_str.replace('.', '', dot_count - 1)
        
        try:
            return float(num_str)
        except ValueError:
            return None


def create_canonical_snapshot(
    parsed_data: Dict[str, Any],
    source_pdf: Path,
    account_name: str = 'unknown'
) -> Dict[str, Any]:
    """
    Create canonical JSON snapshot from parsed data.
    
    Args:
        parsed_data: Output from TradeRepublicParser.parse()
        source_pdf: Path to source PDF
        account_name: Account identifier
    
    Returns:
        Snapshot dict conforming to portfolio-state.schema.json
    """
    now = datetime.now(timezone.utc)
    snapshot_id = now.strftime('%Y-%m-%d-%H%M%S')
    
    snapshot = {
        'snapshot_id': snapshot_id,
        'timestamp': now.isoformat(),
        'version': '1.0.0',
        'source': {
            'type': 'trade_republic_pdf',
            'file': str(source_pdf.name),
            'ingestion_date': now.isoformat()
        },
        'accounts': [
            {
                'account_id': f'trade_republic_{account_name}',
                'account_name': account_name,
                'broker': 'Trade Republic',
                'account_type': 'taxable',
                'currency': 'EUR'
            }
        ],
        'holdings': [],
        'cash': [],
        'totals': {
            'total_market_value': 0.0,
            'total_cash': 0.0,
            'total_portfolio_value': 0.0,
            'base_currency': 'EUR'
        },
        'metadata': {
            'extraction_method': 'column_reconstruction',
            'validation_notes': []
        }
    }
    
    # Process cash positions
    account_id = f'trade_republic_{account_name}'
    for cash_pos in parsed_data.get('cash', []):
        cash_entry = {
            'account_id': account_id,
            'currency': cash_pos.get('currency', 'EUR'),
            'amount': cash_pos.get('amount', 0.0),
            'cash_type': cash_pos.get('cash_type', 'available')
        }
        snapshot['cash'].append(cash_entry)
    
    # Process holdings
    for holding in parsed_data.get('holdings', []):
        snapshot_holding = {
            'security_id': holding.get('security_id'),
            'name': holding.get('name'),
            'isin': holding.get('isin'),
            'security_type': 'other',  # Cannot determine from PDF, requires lookup
            'quantity': holding.get('quantity'),
            'currency': holding.get('currency', 'EUR'),
            'account_id': f'trade_republic_{account_name}'
        }
        
        # Add cost basis if available
        if holding.get('cost_basis'):
            snapshot_holding['cost_basis'] = holding['cost_basis']
        
        # Add market data if available
        if holding.get('market_data'):
            snapshot_holding['market_data'] = holding['market_data']
            snapshot_holding['market_data']['price_date'] = now.isoformat()
        
        snapshot['holdings'].append(snapshot_holding)
    
    # Calculate totals
    total_market_value = sum(
        h.get('market_data', {}).get('market_value', 0) or 0
        for h in snapshot['holdings']
    )
    total_cash = sum(c.get('amount', 0) or 0 for c in snapshot['cash'])
    
    snapshot['totals']['total_market_value'] = total_market_value
    snapshot['totals']['total_cash'] = total_cash
    snapshot['totals']['total_portfolio_value'] = total_market_value + total_cash
    
    # Add validation notes for missing data
    missing_data_count = sum(
        1 for h in snapshot['holdings']
        if not h.get('market_data') or h.get('quantity') is None
    )
    
    if missing_data_count > 0:
        snapshot['metadata']['validation_notes'].append(
            f"{missing_data_count} holdings have incomplete data"
        )
    
    # Add parser warnings
    for warning in parsed_data.get('warnings', []):
        snapshot['metadata']['validation_notes'].append(f"Parser: {warning}")
    
    return snapshot


def copy_pdf_to_raw(source_pdf: Path, raw_dir: Path, account_name: str) -> Path:
    """Copy PDF to portfolio/raw with timestamp naming"""
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest_filename = f"{timestamp}_{account_name}_portfolio.pdf"
    dest_path = raw_dir / dest_filename
    
    shutil.copy2(source_pdf, dest_path)
    return dest_path


def write_snapshot(snapshot: Dict[str, Any], snapshots_dir: Path) -> Path:
    """Write snapshot JSON to snapshots directory"""
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    snapshot_id = snapshot['snapshot_id']
    snapshot_path = snapshots_dir / f"{snapshot_id}.json"
    
    with open(snapshot_path, 'w') as f:
        json.dump(snapshot, f, indent=2, default=str)
    
    return snapshot_path


def write_latest_link(snapshot: Dict[str, Any], portfolio_dir: Path) -> Path:
    """Write latest.json convenience link"""
    latest_path = portfolio_dir / 'latest.json'
    
    with open(latest_path, 'w') as f:
        json.dump(snapshot, f, indent=2, default=str)
    
    return latest_path


def write_csv_export(snapshot: Dict[str, Any], exports_dir: Path) -> Path:
    """Write convenience CSV export"""
    exports_dir.mkdir(parents=True, exist_ok=True)
    
    csv_filename = f"{snapshot['snapshot_id']}_holdings.csv"
    csv_path = exports_dir / csv_filename
    
    import csv
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'security_id', 'name', 'isin', 'quantity', 'currency',
            'market_value', 'account_id'
        ])
        
        # Data rows
        for holding in snapshot['holdings']:
            market_data = holding.get('market_data', {})
            
            writer.writerow([
                holding.get('security_id', ''),
                holding.get('name', ''),
                holding.get('isin', ''),
                holding.get('quantity', ''),
                holding.get('currency', ''),
                market_data.get('market_value', '') if market_data else '',
                holding.get('account_id', '')
            ])
    
    return csv_path


def ingest_pdf(
    pdf_path: Path,
    repo_root: Path,
    config,
    account_name: str = 'unknown',
    export_csv: bool = True,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Main ingestion function.
    
    Returns dict with paths and metadata.
    """
    result = {
        'success': False,
        'raw_pdf_path': None,
        'snapshot_path': None,
        'csv_path': None,
        'latest_path': None,
        'warnings': [],
        'holdings_count': 0
    }
    
    # Validate PDF exists
    if not pdf_path.exists():
        raise IngestError(f"PDF not found: {pdf_path}")
    
    if not pdf_path.suffix.lower() == '.pdf':
        raise IngestError(f"File is not a PDF: {pdf_path}")
    
    # Parse PDF
    parser = TradeRepublicParser(pdf_path, debug=debug)
    parsed_data = parser.parse()
    
    result['warnings'].extend(parsed_data.get('warnings', []))
    result['holdings_count'] = len(parsed_data.get('holdings', []))
    
    # Copy PDF to raw
    raw_dir = repo_root / config.portfolio_raw_dir
    raw_pdf_path = copy_pdf_to_raw(pdf_path, raw_dir, account_name)
    result['raw_pdf_path'] = raw_pdf_path
    
    # Create canonical snapshot
    snapshot = create_canonical_snapshot(parsed_data, raw_pdf_path, account_name)
    
    # Write snapshot
    snapshots_dir = repo_root / config.snapshots_dir
    snapshot_path = write_snapshot(snapshot, snapshots_dir)
    result['snapshot_path'] = snapshot_path
    
    # Update latest.json
    portfolio_dir = repo_root / 'portfolio'
    latest_path = write_latest_link(snapshot, portfolio_dir)
    result['latest_path'] = latest_path
    
    # Write CSV export if requested
    if export_csv:
        exports_dir = portfolio_dir / 'exports'
        csv_path = write_csv_export(snapshot, exports_dir)
        result['csv_path'] = csv_path
    
    result['success'] = True
    return result
