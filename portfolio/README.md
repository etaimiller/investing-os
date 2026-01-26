# Portfolio Directory

This directory contains the current and historical state of your investment portfolio.

## Portfolio Data Architecture: Three Layers

This system maintains a clear separation between raw inputs, canonical data, and convenience formats:

### Layer A: Raw Inputs (Immutable Source of Truth)
**Location**: `portfolio/raw/`

**Primary format**: Trade Republic Portfolio PDFs
- Raw broker statements in original format
- Immutable - never edited after storage
- Complete audit trail of all imported data
- Naming: `trade_republic_<account>_<YYYY-MM-DD>_portfolio.pdf`

See [portfolio/raw/README.md](raw/README.md) for details on raw input formats.

### Layer B: Canonical Normalized Snapshots (Schema-Validated JSON)
**Location**: `portfolio/snapshots/<YYYY-MM-DD-HHMMSS>.json`

**Format**: JSON validated against `schema/portfolio-state.schema.json`
- Single source of truth for all portfolio analysis
- Normalized, validated, machine-readable
- Derived from raw inputs via parsing and normalization (Step 4)
- All downstream analysis uses these canonical snapshots
- Immutable once created - new snapshot for each state change

### Layer C: Convenience Exports (Generated from Canonical JSON)
**Location**: `portfolio/snapshots/<YYYY-MM-DD-HHMMSS>.{csv,md}`

**Formats**: CSV for spreadsheets, Markdown for quick inspection
- Generated from canonical JSON for human readability
- Not the source of truth - can be regenerated anytime
- CSV for importing into spreadsheet tools
- Markdown for quick terminal/editor viewing

## File Naming Convention

- **Raw PDFs**: `trade_republic_<account>_<YYYY-MM-DD>_portfolio.pdf` (in `raw/`)
- **Canonical snapshots**: `YYYY-MM-DD-HHMMSS.json` (e.g., `2024-01-15-143022.json`)
- **CSV exports**: `YYYY-MM-DD-HHMMSS.csv` (generated from JSON)
- **Markdown exports**: `YYYY-MM-DD-HHMMSS.md` (generated from JSON)

## Workflow Integration

1. **Raw Input Storage** - Trade Republic PDF stored in `portfolio/raw/`
2. **PDF Parsing** - Extract holdings, cash, account data from PDF (Step 4)
3. **Data Normalization** - Transform to canonical JSON format
4. **Schema Validation** - Validate against `schema/portfolio-state.schema.json`
5. **Canonical Snapshot** - Store validated JSON in `portfolio/snapshots/`
6. **Convenience Exports** - Generate CSV/MD as needed for viewing
7. **Analysis Input** - Valuations and decisions use canonical JSON snapshots

## When to Look Here

- **Before analysis** - Get current portfolio state
- **After import** - Verify data was processed correctly
- **Historical review** - Track portfolio changes over time
- **Reconciliation** - Ensure holdings match external statements

## Directory Structure

```
portfolio/
├── raw/                # Raw broker statements (primarily PDFs)
│   └── README.md      # Raw input format documentation
├── snapshots/          # Canonical normalized snapshots (JSON)
│   └── template_holdings_snapshot.csv  # CSV mapping aid / convenience format
├── holdings/           # Current and recent holdings data (planned)
├── cash/              # Cash and money market fund balances (planned)
└── statements/        # Processed account statements (planned)
```

## Canonical Data Format

**Canonical snapshots** (Layer B) follow the **portfolio-state.schema.json** schema located in `schema/`.

**Key format principles**:
- JSON format validated against schema
- All data is FACTS from broker or market - no valuations or assumptions
- Market values are DERIVED FACTS (quantity × price) clearly marked
- Cost basis represents historical facts, not current intrinsic value
- All currency amounts include ISO 4217 currency codes (EUR, USD, etc.)

**About the CSV template**:
- `template_holdings_snapshot.csv` is a convenience format / mapping aid
- It shows expected field mapping but is NOT the canonical format
- Canonical format is JSON governed by `schema/portfolio-state.schema.json`
- CSV may be generated from JSON or used as intermediate after PDF parsing

## TODO: User Input Required

**Account Structure:**
- TODO: How many accounts should be tracked?
- TODO: What account types exist (taxable, retirement, etc.)?

**Snapshot Frequency:**
- TODO: How often should portfolio snapshots be created?
- TODO: Should snapshots be created on every data import?

**Data Validation:**
- TODO: What validation rules should be applied to portfolio data?
- TODO: How should data inconsistencies be handled?

## Notes

- All portfolio data is immutable - never modify past snapshots
- Current state is always derived from the latest snapshot
- Historical snapshots provide audit trail for portfolio evolution