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


def is_valid_isin(isin: str) -> bool:
    """
    Validate ISIN using ISO 6166 checksum (Luhn mod-10 algorithm).
    
    ISIN format: 2 letter country code + 9 alphanumeric + 1 check digit
    
    Algorithm:
    1. Convert letters to numbers (A=10, B=11, ..., Z=35)
    2. This creates a string of digits (letters become 2 digits each)
    3. Starting from the rightmost digit, double every second digit going left
    4. Sum all individual digits (if doubling produces 2 digits, sum them separately)
    5. Valid if sum % 10 == 0
    
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
    # Check each char is either digit or uppercase letter
    for char in middle:
        if not (char.isdigit() or (char.isalpha() and char.isupper())):
            return False
    
    # Convert to string of digits: letters A=10, B=11, ..., Z=35
    digit_string = ''
    for char in isin:
        if char.isdigit():
            digit_string += char
        elif char.isalpha() and char.isupper():
            # A=10, B=11, ..., Z=35
            digit_string += str(ord(char) - ord('A') + 10)
        else:
            return False
    
    # Apply Luhn algorithm (mod-10 check)
    # Process individual digits from right to left, doubling every second digit
    total = 0
    for i, digit_char in enumerate(reversed(digit_string)):
        digit = int(digit_char)
        
        # Double every second digit (position 1, 3, 5, ... from right, 0-indexed)
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                # Sum the two digits (e.g., 14 → 1+4=5)
                digit = digit // 10 + digit % 10
        
        total += digit
    
    return total % 10 == 0


class TradeRepublicParser:
    """Parse Trade Republic portfolio PDF"""
    
    # ISIN pattern: 2 letters + 10 alphanumeric
    ISIN_PATTERN = re.compile(r'\b([A-Z]{2}[A-Z0-9]{10})\b')
    
    # Common currency codes in Trade Republic
    CURRENCY_PATTERN = re.compile(r'\b(EUR|USD|GBP|CHF)\b')
    
    def __init__(self, pdf_path: Path, debug: bool = False):
        """Initialize parser with PDF path"""
        if fitz is None:
            raise IngestError(
                "PyMuPDF not installed. Install with: pip install PyMuPDF>=1.23.0"
            )
        
        self.pdf_path = pdf_path
        self.warnings = []
        self.info = {}
        self.debug = debug
        self.isin_candidates = 0
        self.valid_isins = 0
        
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
    
    def _find_holdings_section(self, lines: List[str]) -> Tuple[int, int]:
        """
        Find the holdings section in PDF text.
        Trade Republic uses "POSITIONEN" header for holdings.
        Returns (start_line, end_line) tuple, or (0, len(lines)) if not found.
        """
        start_idx = 0
        end_idx = len(lines)
        
        for i, line in enumerate(lines):
            # Look for "POSITIONEN" (German for "Positions")
            if re.search(r'\bPOSITIONEN\b', line, re.IGNORECASE):
                start_idx = i
                if self.debug:
                    print(f"[DEBUG] Found POSITIONEN header at line {i}")
                break
        
        # Look for section end markers
        for i in range(start_idx, len(lines)):
            # Common end markers in Trade Republic PDFs
            if re.search(r'\b(GESAMT|TOTAL|Summe)\b', lines[i], re.IGNORECASE):
                end_idx = i
                if self.debug:
                    print(f"[DEBUG] Found section end at line {i}")
                break
        
        return start_idx, end_idx
    
    def _find_isin_lines(self, lines: List[str]) -> List[int]:
        """
        Find lines that explicitly mention "ISIN" label.
        Returns list of line indices.
        """
        isin_label_lines = []
        for i, line in enumerate(lines):
            if re.search(r'\bISIN\b', line, re.IGNORECASE):
                isin_label_lines.append(i)
        
        if self.debug and isin_label_lines:
            print(f"[DEBUG] Found {len(isin_label_lines)} lines with 'ISIN' label")
        
        return isin_label_lines
    
    def parse_holdings_table(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse holdings table from PDF text with block-based extraction.
        
        Strategy:
        1. Find holdings section (POSITIONEN)
        2. Find lines with "ISIN" labels
        3. Extract ISIN candidates and validate checksums
        4. For each valid ISIN, extract a block of lines around it
        5. Parse name/quantity/value from the block
        """
        holdings = []
        lines = text.split('\n')
        
        # Find holdings section boundaries
        section_start, section_end = self._find_holdings_section(lines)
        
        # Find lines with "ISIN" labels
        isin_label_lines = self._find_isin_lines(lines)
        
        # Determine search strategy
        if isin_label_lines:
            # If we have explicit ISIN labels, only search near those lines
            search_lines = set()
            for label_line in isin_label_lines:
                # Include ±2 lines around each ISIN label
                for offset in range(-2, 3):
                    line_idx = label_line + offset
                    if section_start <= line_idx < section_end:
                        search_lines.add(line_idx)
            search_lines = sorted(search_lines)
            
            if self.debug:
                print(f"[DEBUG] Searching {len(search_lines)} lines near ISIN labels")
                print(f"[DEBUG] ISIN label lines: {isin_label_lines}")
        else:
            # Fallback: search entire holdings section
            search_lines = list(range(section_start, section_end))
            
            if self.debug:
                print(f"[DEBUG] No ISIN labels found, searching entire section ({section_end - section_start} lines)")
        
        # Track which ISINs we've already processed to avoid duplicates
        processed_isins = set()
        
        # Extract and validate ISINs
        for i in search_lines:
            if i >= len(lines):
                continue
            
            line = lines[i]
            
            # Find ISIN candidates
            for match in self.ISIN_PATTERN.finditer(line):
                candidate = match.group(1)
                self.isin_candidates += 1
                
                # Skip if already processed
                if candidate in processed_isins:
                    continue
                
                # Validate checksum
                if not is_valid_isin(candidate):
                    if self.debug:
                        # Redact for safety - only show format, not full content
                        print(f"[DEBUG] Rejected ISIN candidate: {candidate[:2]}...{candidate[-2:]} (checksum failed)")
                    continue
                
                self.valid_isins += 1
                processed_isins.add(candidate)
                
                if self.debug:
                    # Redacted line preview (no amounts)
                    preview = line[:50].replace(candidate, 'ISIN***')
                    print(f"[DEBUG] Valid ISIN found on line {i}: {candidate[:2]}...{candidate[-2:]} | {preview}...")
                
                # Parse holding using block approach
                holding = self._parse_holding_block(candidate, i, lines, isin_label_lines)
                if holding:
                    holdings.append(holding)
        
        if self.debug:
            print(f"[DEBUG] ISIN candidates: {self.isin_candidates}, valid: {self.valid_isins}, holdings: {len(holdings)}")
        
        return holdings
    
    def _redact_line(self, line: str) -> str:
        """Redact digits in a line for debug output"""
        return re.sub(r'\d', 'X', line)
    
    def _parse_holding_block(self, isin: str, isin_line_idx: int, all_lines: List[str], 
                            isin_label_lines: List[int]) -> Optional[Dict[str, Any]]:
        """
        Parse holding data using block-based extraction around the ISIN line.
        
        Args:
            isin: The validated ISIN
            isin_line_idx: Line index where ISIN was found
            all_lines: All lines from the PDF text
            isin_label_lines: List of line indices with "ISIN" labels
        
        Returns:
            Dict with holding data or None if extraction fails
        """
        # Determine block boundaries
        # Start: Look back up to 8 lines, but stop at empty lines or previous ISIN
        block_start = max(0, isin_line_idx - 8)
        
        # Find previous ISIN line
        prev_isin_line = None
        for label_line in reversed(isin_label_lines):
            if label_line < isin_line_idx:
                prev_isin_line = label_line
                break
        
        # If there's a previous ISIN, don't overlap with it
        if prev_isin_line is not None:
            # Start after previous ISIN, and look for empty line boundary
            candidate_start = prev_isin_line + 1
            
            # Find first empty line after previous ISIN as natural boundary
            for i in range(candidate_start, isin_line_idx):
                if i < len(all_lines) and not all_lines[i].strip():
                    candidate_start = i + 1
                    break
            
            block_start = max(block_start, candidate_start)
        
        # Find next ISIN line for block_end
        next_isin_line = None
        for label_line in isin_label_lines:
            if label_line > isin_line_idx:
                next_isin_line = label_line
                break
        
        if next_isin_line:
            block_end = next_isin_line
        else:
            # Last holding - cap at +20 lines
            block_end = min(len(all_lines), isin_line_idx + 20)
        
        # Extract initial block
        block_lines = all_lines[block_start:block_end]
        
        # Trim block end if we encounter "start of next position" marker
        # Pattern: line starting with number followed by "Stk." / "Stück" / "Anteile"
        # BUT: Only trim if we've already seen at least one such line (the current holding's quantity)
        next_holding_pattern = re.compile(r'^\s*[0-9][0-9\.,]*\s*(Stk\.?|Stück|Anteile)\s*$', re.IGNORECASE)
        
        isin_offset_in_block = isin_line_idx - block_start
        trimmed_end = None
        first_qty_line = None
        
        for i in range(isin_offset_in_block + 1, len(block_lines)):
            if next_holding_pattern.match(block_lines[i]):
                if first_qty_line is None:
                    # This is the current holding's quantity line - keep it
                    first_qty_line = i
                else:
                    # This is the SECOND quantity line - must be next holding
                    trimmed_end = i
                    if self.debug:
                        print(f"[DEBUG] Trimming block at line {block_start + i} (next holding marker)")
                    break
        
        if trimmed_end:
            block_lines = block_lines[:trimmed_end]
        
        block_text = '\n'.join(block_lines)
        
        # Debug output for first 2 holdings only
        if self.debug and len(getattr(self, '_debug_holdings_shown', [])) < 2:
            if not hasattr(self, '_debug_holdings_shown'):
                self._debug_holdings_shown = []
            self._debug_holdings_shown.append(isin)
            
            print(f"\n[DEBUG] Block for ISIN {isin[:2]}...{isin[-2:]} (lines {block_start}-{block_end}):")
            for i, line in enumerate(block_lines[:15]):  # Show first 15 lines max
                redacted = self._redact_line(line)
                print(f"  [{block_start + i:3d}] {redacted[:80]}")
            if len(block_lines) > 15:
                print(f"  ... ({len(block_lines) - 15} more lines)")
        
        # Extract fields (with metadata for debug)
        name = self._extract_name(block_lines, isin_line_idx - block_start, isin)
        quantity, qty_method = self._extract_quantity_with_meta(block_lines, block_start)
        market_value, mv_method = self._extract_market_value_with_meta(block_lines, block_start)
        currency = self._extract_currency(block_text)
        
        # Debug output for extraction methods (first 2 holdings only)
        if self.debug and len(getattr(self, '_debug_holdings_shown', [])) <= 2:
            if qty_method:
                print(f"[DEBUG] Quantity extraction: {qty_method}")
            if mv_method:
                print(f"[DEBUG] Market value extraction: {mv_method}")
        
        # Per-holding warnings
        warnings = []
        if not name or 'ISIN' in name:
            warnings.append(f"Could not extract name for {isin}")
            name = f"Unknown ({isin})"
        if quantity is None:
            warnings.append(f"Could not extract quantity for {isin}")
        if market_value is None:
            warnings.append(f"Could not extract market value for {isin}")
        
        # Add warnings to parser warnings
        for warning in warnings:
            if self.debug:
                print(f"[DEBUG] {warning}")
            self.warnings.append(warning)
        
        return {
            'security_id': isin,
            'isin': isin,
            'name': name,
            'quantity': quantity,
            'currency': currency,
            'cost_basis': None,  # Don't invent cost basis
            'market_data': {
                'market_value': market_value,
                'currency': currency
            } if market_value is not None else None
        }
    
    def _extract_name(self, block_lines: List[str], isin_line_offset: int, isin: str) -> Optional[str]:
        """Extract security name from lines above ISIN (may span multiple lines)"""
        # Patterns for lines that are definitely NOT names (field labels/headers)
        # More restrictive - only match lines that START with these or are mostly these keywords
        field_label_pattern = re.compile(
            r'^\s*(ISIN|WKN|Stück|Stk\.?|Anteile|Kurs|Einstandskurs|Wert|Kurswert|Gesamtwert|'
            r'Gewinn|Verlust|Depot|Positionen|Position|Datum|Seite|Page|Portfolio)\s*[:=]',
            re.IGNORECASE
        )
        
        # Collect potential name lines above ISIN (closest first)
        name_lines = []
        
        for i in range(isin_line_offset - 1, max(-1, isin_line_offset - 5), -1):
            if i < 0 or i >= len(block_lines):
                continue
            
            line = block_lines[i].strip()
            
            # Skip empty lines
            if not line:
                # Empty line signals end of name
                if name_lines:
                    break
                continue
            
            # Skip field label lines (but allow lines that contain currency codes in product names)
            if field_label_pattern.match(line):
                # Stop if we hit a field label
                break
            
            # Skip lines that are mostly numbers (more than 50% digits)
            digit_count = len(re.findall(r'\d', line))
            if digit_count > 0 and digit_count > len(line) // 2:
                continue
            
            # Skip lines that look like they contain ISIN pattern
            if isin in line or re.search(r'\bISIN\s*:', line, re.IGNORECASE):
                continue
            
            # This looks like a name line
            name_lines.insert(0, line)  # Insert at beginning to maintain order
            
            # For now, take only the closest line (most common case)
            # Multi-line names are rare and harder to detect reliably
            break
        
        if name_lines:
            # Join multi-line names with space
            name = ' '.join(name_lines)
            # Clean up extra whitespace
            name = re.sub(r'\s+', ' ', name).strip()
            return name
        
        return None
    
    def _extract_quantity_with_meta(self, block_lines: List[str], block_start: int) -> Tuple[Optional[float], Optional[str]]:
        """
        Extract quantity with metadata about extraction method.
        Returns: (quantity, method_description)
        """
        # Pattern 1: Number-first format (preferred for Trade Republic table layout)
        # Example: "12,345678 Stk."
        number_first_pattern = re.compile(r'^\s*([0-9][0-9\.,]*)\s*(Stk\.?|Stück|Anteile)\s*$', re.IGNORECASE)
        
        # Look for number-first pattern, preferring lines ABOVE where we'd expect ISIN
        # (to avoid catching next holding's quantity)
        for i, line in enumerate(block_lines):
            match = number_first_pattern.match(line)
            if match:
                qty_str = match.group(1)
                qty = self._parse_number(qty_str)
                if qty is not None and qty > 0:
                    line_num = block_start + i
                    return qty, f"number-first line {line_num}"
        
        # Pattern 2: Label-first format (fallback)
        # Example: "Stück 10,00" or "Anteile: 50,00"
        label_first_patterns = [
            r'(?:Stk\.?|Stück|Anteile|Qty|Quantity)\s*[:=]?\s*([0-9][0-9\.,\s]*)',
        ]
        
        block_text = '\n'.join(block_lines)
        for pattern in label_first_patterns:
            match = re.search(pattern, block_text, re.IGNORECASE)
            if match:
                qty_str = match.group(1)
                qty = self._parse_number(qty_str)
                if qty is not None and qty > 0:
                    return qty, "label-first pattern"
        
        return None, None
    
    def _extract_market_value_with_meta(self, block_lines: List[str], block_start: int) -> Tuple[Optional[float], Optional[str]]:
        """
        Extract market value with metadata about extraction method.
        Returns: (market_value, method_description)
        """
        block_text = '\n'.join(block_lines)
        
        # Check if this is a table layout with column headers
        has_kurswert_header = bool(re.search(r'\bKURSWERT\s+IN\s+EUR\b', block_text, re.IGNORECASE))
        
        if has_kurswert_header:
            # Table layout: use column-based extraction
            return self._extract_market_value_column_based(block_lines, block_start)
        
        # Fallback: labeled pattern extraction
        return self._extract_market_value_labeled(block_lines, block_start)
    
    def _extract_market_value_column_based(self, block_lines: List[str], block_start: int) -> Tuple[Optional[float], Optional[str]]:
        """
        Extract market value using column header and date heuristics.
        
        For Trade Republic table layout:
        - Columns: "KURS PRO STÜCK" and "KURSWERT IN EUR"
        - After date, typically see: price-per-unit, then total market value
        - Choose largest as market value
        """
        # Find date lines (DD.MM.YYYY format)
        date_pattern = re.compile(r'\b\d{2}\.\d{2}\.\d{4}\b')
        date_line_idx = None
        
        for i, line in enumerate(block_lines):
            if date_pattern.search(line):
                date_line_idx = i
                break
        
        # Broader money parsing: accept German, plain, and dot-decimal formats
        # Examples: "1.234,56" or "1234,56" or "1234.56"
        money_pattern = re.compile(r'\b([0-9]+(?:[.,][0-9]+)*)\b')
        qty_line_pattern = re.compile(r'^\s*[0-9][0-9\.,]*\s*(Stk\.?|Stück|Anteile)\s*$', re.IGNORECASE)
        
        # Extract all money-like numbers with their line indices
        money_candidates = []
        for i, line in enumerate(block_lines):
            # Skip quantity lines
            if qty_line_pattern.match(line):
                continue
            
            # Find all numbers in this line
            for match in money_pattern.finditer(line):
                num_str = match.group(1)
                # Must have at least one separator (. or ,) to be money-like
                if ',' in num_str or '.' in num_str:
                    num = self._parse_number(num_str)
                    if num is not None and num > 0:
                        money_candidates.append((i, num, num_str))
        
        # Debug output for first 3 holdings
        if self.debug and len(getattr(self, '_debug_holdings_shown', [])) <= 3:
            if date_line_idx is not None:
                print(f"[DEBUG] Date line found at index {date_line_idx}: {block_lines[date_line_idx][:50]}")
            else:
                print(f"[DEBUG] No date line found")
            
            if money_candidates:
                print(f"[DEBUG] Money candidates: {len(money_candidates)}")
                for idx, val, orig_str in money_candidates[:5]:  # Show first 5
                    print(f"[DEBUG]   line {block_start + idx}: {orig_str} -> {val}")
        
        if not money_candidates:
            if self.debug:
                print(f"[DEBUG] No money candidates found")
            return None, None
        
        # NEW HEURISTIC: If there's a date, look at next 4 lines after date
        if date_line_idx is not None:
            # Get candidates from next 4 lines after date
            after_date_candidates = [
                (idx, val, orig_str) for idx, val, orig_str in money_candidates
                if idx > date_line_idx and idx <= date_line_idx + 4
            ]
            
            if len(after_date_candidates) >= 2:
                # Multiple candidates: choose the LARGEST (likely market value, not price-per-unit)
                largest_idx, largest_val, largest_str = max(after_date_candidates, key=lambda x: x[1])
                line_num = block_start + largest_idx
                
                if self.debug and len(getattr(self, '_debug_holdings_shown', [])) <= 3:
                    print(f"[DEBUG] Selected largest of {len(after_date_candidates)} after-date candidates: {largest_val}")
                
                return largest_val, f"largest-after-date line {line_num}"
            
            elif len(after_date_candidates) == 1:
                # Single candidate: use it
                idx, val, orig_str = after_date_candidates[0]
                line_num = block_start + idx
                
                if self.debug and len(getattr(self, '_debug_holdings_shown', [])) <= 3:
                    print(f"[DEBUG] Single candidate after date: {val}")
                
                return val, f"single-after-date line {line_num}"
            
            # else: fall through to no-date fallback
        
        # Fallback: No date or no candidates after date
        # Choose the largest money-like number in entire block (excluding quantity)
        if money_candidates:
            largest_idx, largest_val, largest_str = max(money_candidates, key=lambda x: x[1])
            line_num = block_start + largest_idx
            
            if self.debug and len(getattr(self, '_debug_holdings_shown', [])) <= 3:
                if date_line_idx is None:
                    print(f"[DEBUG] No date - using largest in block: {largest_val}")
                else:
                    print(f"[DEBUG] No candidates after date - using largest in block: {largest_val}")
            
            # Add warning if date was expected but missing
            if date_line_idx is None and hasattr(self, 'warnings'):
                # Only warn once per parse
                if not hasattr(self, '_warned_no_date'):
                    self.warnings.append("No date lines found in table layout, using fallback for market value")
                    self._warned_no_date = True
            
            return largest_val, f"largest-in-block line {line_num}"
        
        return None, None
    
    def _extract_market_value_labeled(self, block_lines: List[str], block_start: int) -> Tuple[Optional[float], Optional[str]]:
        """Extract market value using labeled patterns (fallback)"""
        block_text = '\n'.join(block_lines)
        
        # Try labeled patterns first (DE + EN)
        value_patterns = [
            r'(?:Wert|Kurswert|Gesamtwert)\s*[:=]?\s*([0-9][0-9\.,\s]*)\s*(?:EUR|USD|GBP|CHF)',
            r'(?:Value|Market Value)\s*[:=]?\s*([0-9][0-9\.,\s]*)\s*(?:EUR|USD|GBP|CHF)',
        ]
        
        for pattern in value_patterns:
            match = re.search(pattern, block_text, re.IGNORECASE)
            if match:
                value_str = match.group(1)
                value = self._parse_number(value_str)
                if value is not None and value > 0:
                    return value, "labeled-pattern"
        
        # Fallback: Look for lines with "Wert" or "Value" and extract number
        for i, line in enumerate(block_lines):
            if re.search(r'\b(Wert|Kurswert|Gesamtwert|Value)\b', line, re.IGNORECASE):
                # Extract number with currency from this line only
                number_pattern = re.compile(r'([0-9][0-9\.,\s]*)\s*(?:EUR|USD|GBP|CHF)')
                match = number_pattern.search(line)
                if match:
                    value_str = match.group(1)
                    value = self._parse_number(value_str)
                    if value is not None and value > 0:
                        line_num = block_start + i
                        return value, f"wert-line line {line_num}"
        
        return None, None
    
    def _extract_currency(self, block_text: str) -> str:
        """Extract currency code from block, default to EUR"""
        match = self.CURRENCY_PATTERN.search(block_text)
        return match.group(1) if match else 'EUR'
    
    def _parse_number(self, num_str: str) -> Optional[float]:
        """Parse number string handling German/European formatting"""
        if not num_str:
            return None
        
        # Remove spaces
        num_str = num_str.strip().replace(' ', '')
        
        # Handle different decimal formats
        # German: 1.234,56 or 1234,56
        # English: 1,234.56 or 1234.56
        
        # Count commas and dots
        comma_count = num_str.count(',')
        dot_count = num_str.count('.')
        
        if comma_count > 0 and dot_count > 0:
            # Both present - determine which is decimal separator
            last_comma_pos = num_str.rfind(',')
            last_dot_pos = num_str.rfind('.')
            
            if last_comma_pos > last_dot_pos:
                # German format: 1.234,56
                num_str = num_str.replace('.', '').replace(',', '.')
            else:
                # English format: 1,234.56
                num_str = num_str.replace(',', '')
        elif comma_count > 1:
            # Multiple commas - thousand separators: 1,234,567
            num_str = num_str.replace(',', '')
        elif dot_count > 1:
            # Multiple dots - thousand separators: 1.234.567
            num_str = num_str.replace('.', '', dot_count - 1)
        elif comma_count == 1:
            # Single comma - likely decimal: 1234,56
            num_str = num_str.replace(',', '.')
        
        try:
            return float(num_str)
        except ValueError:
            return None
    
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
