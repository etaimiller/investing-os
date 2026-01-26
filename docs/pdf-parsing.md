# Trade Republic PDF Parsing Guide

## Expected PDF Format

The ingestion system expects Trade Republic portfolio PDFs with the following structure:

### 1. Holdings Table

**Expected columns/data**:
- Security name (e.g., "Apple Inc.")
- ISIN (e.g., "US0378331005") - **Required for reliable parsing**
- Quantity (number of shares)
- Average buy price
- Current price
- Current market value
- Gain/loss (optional)

**Example text pattern**:
```
Apple Inc.        US0378331005    10    150.00    175.50    1755.00    +255.00
```

### 2. Cash Position

**Keywords to look for**: "Cash", "Guthaben", "Verfügbar", "Available"

**Example**:
```
Cash: 1,234.56 EUR
```

### 3. Currency

Default currency is EUR (Trade Republic base currency).
USD, GBP, CHF also supported if found in text.

## What the Parser Does

### Text Extraction
- Uses PyMuPDF (fitz) to extract all text from PDF
- Processes all pages in multi-page PDFs
- Detects if PDF is scanned (minimal text) and reports error

### Pattern Matching
- **ISIN Detection**: Looks for pattern `[A-Z]{2}[A-Z0-9]{10}` with ISO 6166 checksum validation
  - Uses Luhn mod-10 algorithm to validate ISIN checksums
  - Rejects false positives (e.g., "BRUNNENSTRASSE" from street names)
  - Prioritizes ISINs near explicit "ISIN" labels in the text
- **Number Extraction**: Finds numeric values with decimals and thousand separators
- **Currency Detection**: Identifies EUR, USD, GBP, CHF

### Data Extraction per Holding
For each line containing a valid ISIN:
1. Find "POSITIONEN" section (holdings table boundaries)
2. Search for explicit "ISIN" labels and prioritize nearby ISINs (±2 lines)
3. Validate ISIN checksums using ISO 6166 standard (Luhn mod-10 algorithm)
4. Extract security name (text before ISIN)
5. Extract numbers from line
6. Map numbers to fields (heuristic):
   - If 4+ numbers: quantity, avg_price, current_price, market_value
   - If 2-3 numbers: quantity and market_value (at minimum)
7. Detect currency (default EUR if not found)

**Debug Mode**: Use `investos ingest --debug-parse` to see detailed parsing output including:
- Holdings section boundaries
- ISIN candidates and validation results
- Fallback behavior when no explicit ISIN labels found

### Cash Position
- Searches for cash keywords
- Extracts amount (typically last number on line)
- Detects currency

## Handling Missing Data

### Strategy: Prefer Correctness Over Completeness

**Missing values are set to `null` with warnings**:
- Missing cost basis → `cost_basis: null` + warning
- Missing current price → `market_data: null` + warning
- Missing cash position → `cash: []` + warning
- No holdings found → Empty holdings array + warning

**All warnings are logged in**:
- Snapshot JSON `metadata.validation_notes`
- CLI output during ingestion
- Run log JSON file

### Example Warning
```
⚠ Could not extract cash position from PDF
⚠ 2 holdings have incomplete data (missing prices or cost basis)
```

## Limitations & Known Issues

### Current Version (v1)
- ✅ Digital PDFs only (text-based)
- ✅ Standard Trade Republic format
- ✅ Holdings with ISINs
- ❌ Scanned PDFs (OCR not yet implemented)
- ❌ Non-standard formats
- ❌ Securities without ISINs (rare)

### Parsing Heuristics
The parser uses heuristics to map extracted numbers to fields. This works well for standard Trade Republic PDFs but may struggle with:
- Unusual formatting
- Multi-line holdings
- Special characters in security names
- Holdings with very long names

**ISIN Validation Strategy**:
1. First pass: Find lines near explicit "ISIN" labels (most reliable)
2. Second pass: Find all ISIN pattern matches in holdings section
3. Validate each candidate using ISO 6166 checksum (rejects ~90% of false positives)
4. This prevents false matches like "BRUNNENSTRASSE" from German street addresses

### When Parsing Fails
If parsing produces incorrect results:
1. Check PDF is digital (not scanned)
2. Verify it's a Trade Republic portfolio PDF
3. Check for unusual formatting
4. Review warnings in output
5. Inspect generated snapshot JSON manually

## Testing Without Real PDFs

Since real PDFs contain sensitive data, use the test suite:

```bash
# Run tests with mocked data
python3 -m unittest tests/test_ingest.py
```

Tests verify:
- Snapshot structure conforms to schema
- Holdings and cash are correctly mapped
- Totals are calculated
- Missing data is handled gracefully
- JSON serialization works

## Future Improvements (TODO)

1. **OCR Support**: Handle scanned PDFs
2. **Better Pattern Matching**: More robust parsing of various layouts
3. **Security Type Detection**: Distinguish stocks from ETFs automatically
4. **Multi-Currency Handling**: Better support for non-EUR holdings
5. **Transaction History**: Parse transactions, not just current positions
6. **Validation Against Market Data**: Optional price verification
