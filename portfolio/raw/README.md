# Portfolio Raw Inputs Directory

This directory contains raw, unprocessed broker statements and exports in their original formats.

## Primary Input Format: PDFs

**Trade Republic Portfolio PDFs are the primary raw input format for this system.**

Raw broker statements are stored here as immutable files. These files are never edited after import - they serve as the source of truth for all portfolio data processing.

## What Belongs Here

- **Trade Republic Portfolio PDFs** - Primary input format
- **Other broker statements** - PDFs from other brokers (if applicable)
- **CSV exports** - Alternative format if provided by broker
- **Account statements** - Monthly or quarterly statements in original format

## File Naming Convention

### Trade Republic Portfolio PDFs (Primary)
```
trade_republic_<account>_<YYYY-MM-DD>_portfolio.pdf
```

**Examples**:
- `trade_republic_main_2024-01-15_portfolio.pdf`
- `trade_republic_retirement_2024-01-15_portfolio.pdf`

### Other Formats (If Applicable)
```
<broker>_<account>_<YYYY-MM-DD>_<type>.<ext>
```

**Examples**:
- `trade_republic_main_2024-01-15_transactions.pdf`
- `trade_republic_main_2024-01-15_export.csv`

## Workflow: Raw Input to Canonical Snapshot

```
1. Raw Input (Immutable)
   └─> portfolio/raw/trade_republic_main_2024-01-15_portfolio.pdf
   
2. PDF Parsing (Step 4)
   └─> Extract holdings, cash, transactions data
   
3. Data Normalization (Step 4)
   └─> Transform to canonical JSON format
   
4. Canonical Snapshot (Schema-Validated)
   └─> portfolio/snapshots/2024-01-15-143022.json
        Validated against schema/portfolio-state.schema.json
        
5. Convenience Exports (Optional)
   └─> portfolio/snapshots/2024-01-15-143022.csv (for spreadsheet viewing)
   └─> portfolio/snapshots/2024-01-15-143022.md (for quick inspection)
```

## File Management Principles

### Immutability
- **NEVER edit raw files** - they are the source of truth
- **NEVER delete raw files** - maintain complete audit trail
- **NEVER overwrite raw files** - use unique timestamps in filenames

### Organization
- One file per account per date per document type
- Use consistent naming convention for automated processing
- Keep files in chronological order (filename sorting)

### Storage
- Raw files are excluded from git (see `.gitignore`)
- Raw files should be backed up separately
- Consider encryption for sensitive broker statements

## Data Privacy

**IMPORTANT**: Raw broker statements contain sensitive personal financial information.

- Raw PDFs are **NOT committed to git** (excluded via `.gitignore`)
- Only processed, normalized snapshots (with PII considerations) should be versioned
- Consider encryption at rest for raw file storage
- Be cautious when sharing repository or files

## Trade Republic PDF Format

**Expected sections in Trade Republic Portfolio PDF**:
- Account summary with total portfolio value
- Holdings list with:
  - Security name
  - ISIN
  - Quantity
  - Average buy price
  - Current price
  - Current value
  - Gain/loss
- Cash position
- Account information

**PDF Parsing Notes** (for Step 4 implementation):
- Trade Republic PDFs use standard formatting
- ISINs are consistently included
- Prices typically in EUR
- Watch for multi-page documents with holdings split across pages
- Cash position usually at bottom of holdings table

## TODO: User Input Required

**Broker Details**:
- TODO: Confirm Trade Republic PDF format is as expected
- TODO: Are there multiple Trade Republic accounts to track?
- TODO: What account naming convention should be used?

**File Organization**:
- TODO: How should historical statements be organized (by year/quarter)?
- TODO: Should transaction CSVs also be stored here or separately?
- TODO: What retention policy for raw statements (keep all, archive old, etc.)?

**Data Privacy**:
- TODO: Should raw PDFs be encrypted at rest?
- TODO: What backup strategy for raw statements?
- TODO: Any compliance requirements for financial document retention?

## Future Formats

This directory may later include:
- Other broker statement formats (PDFs, CSVs, APIs)
- Bank statements for cash account tracking
- Tax documents for cost basis verification
- Corporate action notifications

The ingestion system (Step 4) will be designed to handle multiple input formats, but Trade Republic Portfolio PDFs are the primary focus.

## Notes

- Raw files are the ultimate source of truth - canonical snapshots are derived
- Multiple raw files may be processed into a single canonical snapshot
- Canonical snapshots are what the rest of the system operates on
- Always prefer PDF when available - it's the broker's official statement
- CSV exports are secondary and may have less detail than PDFs