"""
Portfolio ingestion from Trade Republic PDFs

Extracts holdings data from Trade Republic portfolio PDFs and creates
canonical JSON snapshots conforming to schema/portfolio-state.schema.json

Trade Republic PDF Format:
- Contains account summary with total portfolio value
- Holdings table with: Name, ISIN, Quantity, Avg Buy Price, Current Price, Current Value, Gain/Loss
- Cash position typically at bottom
- May span multiple pages

Parsing Strategy:
- Extract all text from PDF
- Identify holdings table by looking for ISIN patterns
- Parse rows extracting: name, ISIN, quantity, prices, values
- Handle missing/malformed data gracefully with warnings
"""

import re
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


class IngestError(Exception):
    """Error during PDF ingestion"""
    pass


class TradeRepublicParser:
    """Parse Trade Republic portfolio PDF"""
    
    # ISIN pattern: 2 letters + 10 alphanumeric
    ISIN_PATTERN = re.compile(r'\b([A-Z]{2}[A-Z0-9]{10})\b')
    
    # Common currency codes in Trade Republic
    CURRENCY_PATTERN = re.compile(r'\b(EUR|USD|GBP|CHF)\b')
    
    def __init__(self, pdf_path: Path):
        """Initialize parser with PDF path"""
        if fitz is None:
            raise IngestError(
                "PyMuPDF not installed. Install with: pip install PyMuPDF>=1.23.0"
            )
        
        self.pdf_path = pdf_path
        self.warnings = []
        self.info = {}
        
    def extract_text(self) -> str:
        """Extract all text from PDF"""
        try:
            doc = fitz.open(str(self.pdf_path))
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_parts.append(page.get_text())
            
            doc.close()
            return "\n".join(text_parts)
        
        except Exception as e:
            raise IngestError(f"Failed to extract PDF text: {e}")
    
    def detect_scanned_pdf(self, text: str) -> bool:
        """Check if PDF appears to be scanned (very little text)"""
        # If less than 100 characters extracted, likely scanned
        return len(text.strip()) < 100
    
    def parse_holdings_table(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse holdings table from PDF text.
        
        Expected format (approximate):
        Name              ISIN         Qty    Avg Buy  Curr Price  Value    Gain/Loss
        Apple Inc.        US0378331005  10    150.00   175.50     1755.00   +255.00
        """
        holdings = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Look for lines containing ISINs
            isin_match = self.ISIN_PATTERN.search(line)
            if not isin_match:
                continue
            
            isin = isin_match.group(1)
            
            # Try to extract other fields from this line and surrounding context
            holding = self._parse_holding_row(line, isin, lines, i)
            if holding:
                holdings.append(holding)
        
        return holdings
    
    def _parse_holding_row(self, line: str, isin: str, all_lines: List[str], line_idx: int) -> Optional[Dict[str, Any]]:
        """Parse a single holding row"""
        # Try to extract numeric values from line
        # Look for patterns like: 10 150.00 175.50 1755.00
        
        # Remove ISIN from line for cleaner parsing
        cleaned_line = line.replace(isin, ' ')
        
        # Extract all numbers (with optional decimals and thousand separators)
        number_pattern = re.compile(r'[-+]?\d{1,3}(?:[,.\s]\d{3})*(?:[.,]\d+)?')
        numbers = number_pattern.findall(cleaned_line)
        
        # Clean numbers (remove thousand separators, convert decimal comma to dot)
        cleaned_numbers = []
        for num in numbers:
            # Remove spaces and thousand separators
            num = num.replace(' ', '').replace(',', '.')
            # Handle German format (comma as decimal)
            if '.' in num and num.count('.') > 1:
                # Multiple dots means they're thousand separators
                num = num.replace('.', '', num.count('.') - 1)
            try:
                cleaned_numbers.append(float(num))
            except ValueError:
                continue
        
        # Try to extract security name (text before ISIN)
        isin_pos = line.find(isin)
        name = line[:isin_pos].strip() if isin_pos > 0 else f"Unknown ({isin})"
        
        # Guess which numbers are which based on typical Trade Republic format
        # Expected: quantity, avg_price, current_price, market_value, gain_loss
        quantity = None
        avg_price = None
        current_price = None
        market_value = None
        
        if len(cleaned_numbers) >= 4:
            # Likely have: qty, avg_buy, curr_price, value
            quantity = cleaned_numbers[0]
            avg_price = cleaned_numbers[1]
            current_price = cleaned_numbers[2]
            market_value = cleaned_numbers[3]
        elif len(cleaned_numbers) >= 2:
            # At minimum we might have quantity and value
            quantity = cleaned_numbers[0]
            market_value = cleaned_numbers[-1]
        
        # Detect currency (default to EUR for Trade Republic)
        currency_match = self.CURRENCY_PATTERN.search(line)
        currency = currency_match.group(1) if currency_match else 'EUR'
        
        return {
            'security_id': isin,
            'isin': isin,
            'name': name,
            'quantity': quantity,
            'currency': currency,
            'cost_basis': {
                'average_price': avg_price,
                'total_cost': quantity * avg_price if (quantity and avg_price) else None,
                'currency': currency
            } if avg_price else None,
            'market_data': {
                'price': current_price,
                'market_value': market_value,
                'currency': currency
            } if current_price or market_value else None
        }
    
    def parse_cash_position(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Try to extract cash position from PDF.
        Usually labeled "Cash" or "Guthaben" with amount in EUR.
        """
        lines = text.split('\n')
        
        for line in lines:
            # Look for cash-related keywords
            if re.search(r'\b(Cash|Guthaben|Verfügbar|Available)\b', line, re.IGNORECASE):
                # Extract amount
                number_pattern = re.compile(r'([-+]?\d{1,3}(?:[,.\s]\d{3})*(?:[.,]\d+)?)')
                matches = number_pattern.findall(line)
                
                if matches:
                    amount_str = matches[-1]  # Usually the last number
                    # Clean up
                    amount_str = amount_str.replace(' ', '').replace(',', '.')
                    try:
                        amount = float(amount_str)
                        
                        # Detect currency
                        currency_match = self.CURRENCY_PATTERN.search(line)
                        currency = currency_match.group(1) if currency_match else 'EUR'
                        
                        return {
                            'currency': currency,
                            'amount': amount,
                            'cash_type': 'available'
                        }
                    except ValueError:
                        pass
        
        self.warnings.append("Could not extract cash position from PDF")
        return None
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse PDF and return intermediate data structure.
        
        Returns dict with:
        - holdings: List of holding dicts
        - cash: Cash position dict (if found)
        - warnings: List of warning messages
        - metadata: PDF metadata
        """
        # Extract text
        text = self.extract_text()
        
        # Check if scanned
        if self.detect_scanned_pdf(text):
            raise IngestError(
                "PDF appears to be scanned (very little text extracted). "
                "OCR support is not yet implemented. "
                "Please use a digital PDF export from Trade Republic."
            )
        
        # Parse holdings
        holdings = self.parse_holdings_table(text)
        
        if not holdings:
            self.warnings.append(
                "No holdings found in PDF. Check if format matches expected Trade Republic layout."
            )
        
        # Parse cash
        cash = self.parse_cash_position(text)
        
        # Store metadata
        self.info['holdings_count'] = len(holdings)
        self.info['has_cash'] = cash is not None
        
        return {
            'holdings': holdings,
            'cash': [cash] if cash else [],
            'warnings': self.warnings,
            'metadata': {
                'source_pdf': str(self.pdf_path.name),
                'pdf_pages': self._count_pages(),
                'extraction_method': 'pymupdf'
            }
        }
    
    def _count_pages(self) -> int:
        """Count pages in PDF"""
        try:
            doc = fitz.open(str(self.pdf_path))
            count = len(doc)
            doc.close()
            return count
        except:
            return 0


def create_canonical_snapshot(
    parsed_data: Dict[str, Any],
    source_pdf_path: Path,
    account_name: str = 'unknown'
) -> Dict[str, Any]:
    """
    Create canonical snapshot JSON from parsed data.
    Conforms to schema/portfolio-state.schema.json structure.
    """
    now = datetime.now(timezone.utc)
    snapshot_id = now.strftime('%Y-%m-%d-%H%M%S')
    
    # Build snapshot structure
    snapshot = {
        'snapshot_id': snapshot_id,
        'timestamp': now.isoformat(),
        'version': '1.0.0',
        'source': {
            'broker': 'Trade Republic',
            'export_date': now.strftime('%Y-%m-%d'),
            'import_method': 'pdf_ingestion',
            'source_file': str(source_pdf_path.name)
        },
        'accounts': [
            {
                'account_id': f'trade_republic_{account_name}',
                'account_type': 'taxable',  # Trade Republic is typically taxable
                'account_name': f'Trade Republic ({account_name})',
                'currency': 'EUR'  # Trade Republic base currency
            }
        ],
        'holdings': [],
        'cash': parsed_data.get('cash', []),
        'totals': {
            'base_currency': 'EUR',
            'total_market_value': 0.0,
            'total_cash': 0.0,
            'total_portfolio_value': 0.0
        },
        'metadata': {
            'validation_status': 'pending',
            'validation_notes': [],
            'notes': f"Imported from {source_pdf_path.name}"
        }
    }
    
    # Add account_id to cash positions
    for cash_item in snapshot['cash']:
        cash_item['account_id'] = snapshot['accounts'][0]['account_id']
    
    # Process holdings
    account_id = snapshot['accounts'][0]['account_id']
    
    for holding in parsed_data.get('holdings', []):
        snapshot_holding = {
            'security_id': holding.get('security_id'),
            'security_type': 'stock',  # Default to stock, TODO: detect ETFs
            'name': holding.get('name'),
            'isin': holding.get('isin'),
            'quantity': holding.get('quantity'),
            'currency': holding.get('currency', 'EUR'),
            'account_id': account_id
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
        if not h.get('market_data') or not h.get('cost_basis')
    )
    
    if missing_data_count > 0:
        snapshot['metadata']['validation_notes'].append(
            f"{missing_data_count} holdings have incomplete data (missing prices or cost basis)"
        )
    
    # Add parser warnings
    for warning in parsed_data.get('warnings', []):
        snapshot['metadata']['validation_notes'].append(f"Parser warning: {warning}")
    
    return snapshot


def copy_pdf_to_raw(
    source_pdf: Path, 
    raw_dir: Path, 
    account_name: str
) -> Path:
    """
    Copy PDF to portfolio/raw with proper naming.
    Returns the destination path.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename: trade_republic_<account>_<YYYY-MM-DD-HHMMSS>_portfolio.pdf
    now = datetime.now(timezone.utc)
    timestamp = now.strftime('%Y-%m-%d-%H%M%S')
    dest_filename = f"trade_republic_{account_name}_{timestamp}_portfolio.pdf"
    dest_path = raw_dir / dest_filename
    
    # Copy file
    shutil.copy2(source_pdf, dest_path)
    
    return dest_path


def write_snapshot(snapshot: Dict[str, Any], snapshots_dir: Path) -> Path:
    """Write canonical snapshot JSON"""
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    snapshot_filename = f"{snapshot['snapshot_id']}.json"
    snapshot_path = snapshots_dir / snapshot_filename
    
    with open(snapshot_path, 'w') as f:
        json.dump(snapshot, f, indent=2, default=str)
    
    return snapshot_path


def write_latest_link(snapshot: Dict[str, Any], portfolio_dir: Path) -> Path:
    """Write latest.json pointing to most recent snapshot"""
    latest_path = portfolio_dir / 'latest.json'
    
    latest_data = {
        'snapshot_id': snapshot['snapshot_id'],
        'timestamp': snapshot['timestamp'],
        'snapshot_file': f"snapshots/{snapshot['snapshot_id']}.json"
    }
    
    with open(latest_path, 'w') as f:
        json.dump(latest_data, f, indent=2)
    
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
            'avg_price', 'current_price', 'market_value', 'cost_basis'
        ])
        
        # Data rows
        for holding in snapshot['holdings']:
            cost_basis = holding.get('cost_basis', {})
            market_data = holding.get('market_data', {})
            
            writer.writerow([
                holding.get('security_id', ''),
                holding.get('name', ''),
                holding.get('isin', ''),
                holding.get('quantity', ''),
                holding.get('currency', ''),
                cost_basis.get('average_price', '') if cost_basis else '',
                market_data.get('price', '') if market_data else '',
                market_data.get('market_value', '') if market_data else '',
                cost_basis.get('total_cost', '') if cost_basis else ''
            ])
    
    return csv_path


def ingest_pdf(
    pdf_path: Path,
    repo_root: Path,
    config,
    account_name: str = 'unknown',
    export_csv: bool = True
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
    parser = TradeRepublicParser(pdf_path)
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
