# Portfolio Directory

This directory contains the current and historical state of your investment portfolio.

## What Belongs Here

- **Portfolio snapshots** - Timestamped JSON files representing complete portfolio state
- **Holdings data** - Current positions across all accounts
- **Cash balances** - Available cash and money market funds
- **Account statements** - Imported and processed account data

## File Naming Convention

- **Snapshots**: `YYYY-MM-DD-HHMMSS.json` (e.g., `2024-01-15-143022.json`)
- **Holdings**: `holdings-YYYY-MM-DD.json`
- **Statements**: `statement-YYYY-MM-DD.json`

## Workflow Integration

1. **Data Import** - Raw data comes in from Trade Republic exports
2. **Snapshot Creation** - Create normalized snapshot after each import
3. **State Tracking** - Historical snapshots provide portfolio evolution
4. **Analysis Input** - Valuations and decisions use current snapshot data

## When to Look Here

- **Before analysis** - Get current portfolio state
- **After import** - Verify data was processed correctly
- **Historical review** - Track portfolio changes over time
- **Reconciliation** - Ensure holdings match external statements

## Directory Structure

```
portfolio/
├── snapshots/          # Historical portfolio snapshots
├── holdings/           # Current and recent holdings data
├── cash/              # Cash and money market fund balances
└── statements/        # Processed account statements
```

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