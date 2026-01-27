# Valuation Outputs Directory

This directory contains **generated valuation results** produced by the `investos value` command.

## Purpose

All valuation analysis outputs are written here automatically. These files should **never be edited manually** - they are generated artifacts derived from portfolio snapshots and assumptions.

## Output File Types

### 1. Per-Holding Valuation Files

**Format**: `<ISIN>-valuation.json`
**Example**: `US0378331005-valuation.json`

Each holding in the portfolio gets its own valuation output file containing:

- Valuation metadata (ID, timestamp, version)
- Security identification (ISIN, name, type)
- Facts (market value, quantity, currency)
- Assumptions used (discount rate, growth rates, margin of safety)
- Calculated values (intrinsic value range, implied upside)
- Methodology applied
- Warnings and data quality issues
- Links to supporting research and decision memos

### 2. Portfolio Summary File

**Format**: `portfolio_summary.json`

Aggregated portfolio-level analysis containing:

- Portfolio metrics (total value, cash, holdings count)
- Position sizing analysis (all holdings with weights)
- Top holdings by weight
- Concentration risk flags (positions >10%)
- Valuation status summary (complete/incomplete counts)
- All warnings aggregated from individual holdings

### 3. Timestamped Run Directories

Each valuation run creates a timestamped subdirectory:

```
outputs/
├── 20240127_143022/
│   ├── US0378331005-valuation.json
│   ├── IE00B4L5Y983-valuation.json
│   ├── ...
│   └── portfolio_summary.json
└── 20240128_091544/
    └── ...
```

This allows tracking valuation changes over time and comparing assumptions.

## Git Ignore

**This directory is git-ignored** (except this README.md) because outputs contain:
- Personal portfolio composition
- Specific holdings and position sizes
- Derived financial analysis of your investments

- ✓ README.md is tracked
- ✗ All timestamped subdirectories are ignored
- ✗ All .json output files are ignored

If you want to commit sanitized example outputs for testing:
```bash
git add -f valuations/outputs/example-output.json
```

## Regeneration

Output files should be treated as **ephemeral**. You can safely delete them and regenerate:

```bash
# Delete old outputs
rm -rf valuations/outputs/2024*

# Regenerate from latest snapshot
./bin/investos value --snapshot portfolio/latest.json
```

The system will recreate all outputs from the canonical snapshot and assumptions.

## Schema Compliance

All output files conform to:
- `schema/valuation-model.schema.json` (per-holding)
- Portfolio summary uses documented structure (no formal schema yet)

Validate outputs:
```bash
./bin/investos validate \
  --file valuations/outputs/20240127_143022/US0378331005-valuation.json \
  --schema schema/valuation-model.schema.json
```

## Reproducibility

Given identical inputs (snapshot + assumptions), the valuation engine produces **deterministic outputs**:
- Same intrinsic values
- Same classifications (undervalued/fair/overvalued)
- Same warnings

Only timestamps and generated IDs will differ between runs.

## Usage in Workflow

Outputs feed into:
1. **Monitoring** - Track valuation changes over time
2. **Decision memos** - Link to supporting valuation analysis
3. **Portfolio reviews** - Identify concentration risks and rebalancing needs
4. **Assumption validation** - Compare actual outcomes to projected values
