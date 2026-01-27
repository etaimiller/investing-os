# Portfolio Change Explanations

This directory contains **generated portfolio change attribution reports** produced by the `investos explain` command.

## Purpose

The explain engine performs deterministic, offline analysis of portfolio changes between two snapshots. It answers: **"What mechanically drove the change in my portfolio value between snapshot A and snapshot B?"**

This is NOT market commentary or news analysis. It's pure mechanical attribution based on snapshot data.

## Attribution Categories

### 1. Price Change
**Mechanical definition**: Same holding, same quantity, different market value.

**What it means**: The market value per share changed between snapshots. This could be due to:
- Share price movement
- Currency fluctuation (if security is denominated in foreign currency)
- Broker valuation updates

**Example**: You own 100 shares, owned 100 shares before, but total value increased from €1,800 to €2,000.

### 2. Quantity Change
**Mechanical definition**: Same holding, different quantity, different market value.

**What it means**: You bought or sold shares. The contribution includes both:
- The effect of quantity change
- Any price movement during the period

**Note**: Without intraday prices, we cannot perfectly separate quantity vs price effects. The total delta is attributed to quantity_change as the dominant mechanical driver.

**Example**: You owned 50 shares worth €4,200, now own 60 shares worth €5,100 (bought 10 shares + price moved).

### 3. New Position
**Mechanical definition**: Holding exists in snapshot B but not in snapshot A.

**What it means**: You opened a new position (bought a security you didn't own before).

**Contribution**: Full market value in snapshot B.

### 4. Position Removed
**Mechanical definition**: Holding exists in snapshot A but not in snapshot B.

**What it means**: You closed an existing position (sold all shares).

**Contribution**: Negative of full market value from snapshot A.

### 5. Cash Change
**Mechanical definition**: Cash balance changed between snapshots.

**What it means**: Cash increased (deposit, dividend, sale proceeds) or decreased (withdrawal, purchase).

**Per account + currency**: Tracked separately for each account/currency combination.

### 6. FX Effect
**Mechanical definition**: Portfolio valued in different currencies shows currency-driven changes.

**What it means**: Exchange rate movements affected portfolio value when holdings are in multiple currencies.

**Note**: Only computed if both snapshots explicitly track multi-currency effects. Otherwise skipped.

### 7. Residual Unexplained
**Mechanical definition**: Portfolio delta minus sum of all explained drivers.

**What it means**: 
- Rounding errors
- Timing differences (snapshot taken at different times of day)
- Broker fee deductions
- Dividend accruals
- Data quality issues

**Expected**: Should be small (<0.5% of total delta). Large residuals indicate data quality problems.

## Output Files

Each explanation run creates a timestamped directory:

```
monitoring/explanations/
├── 20240128_143022/
│   ├── explanation.json        # Machine-readable attribution report
│   └── explanation.md          # Optional human-readable summary
└── 20240129_091544/
    └── ...
```

### explanation.json Structure

```json
{
  "report_id": "explanation-20240128-143022",
  "generated_at": "2024-01-28T14:30:22Z",
  "from_snapshot": {
    "path": "portfolio/snapshots/2024-01-15-120000.json",
    "snapshot_id": "2024-01-15-120000",
    "timestamp": "2024-01-15T12:00:00Z"
  },
  "to_snapshot": {
    "path": "portfolio/snapshots/2024-01-22-120000.json",
    "snapshot_id": "2024-01-22-120000",
    "timestamp": "2024-01-22T12:00:00Z"
  },
  "totals": {
    "from_total": 50000.00,
    "to_total": 52500.00,
    "delta_abs": 2500.00,
    "delta_pct": 0.05,
    "base_currency": "EUR",
    "totals_source": "from_snapshot"
  },
  "drivers": [
    {
      "type": "price_change",
      "account_id": "main",
      "isin": "US0378331005",
      "name": "Apple Inc.",
      "contribution_abs": 1800.00,
      "contribution_pct_of_portfolio_delta": 0.72,
      "details": {
        "quantity_A": 100,
        "quantity_B": 100,
        "mv_A": 18000.00,
        "mv_B": 19800.00,
        "notes": "Quantity unchanged, value increased"
      }
    },
    {
      "type": "new_position",
      "account_id": "main",
      "isin": "IE00B4L5Y983",
      "name": "iShares Core MSCI World UCITS ETF",
      "contribution_abs": 500.00,
      "contribution_pct_of_portfolio_delta": 0.20,
      "details": {
        "mv_B": 500.00,
        "notes": "New position opened"
      }
    },
    {
      "type": "residual_unexplained",
      "contribution_abs": 200.00,
      "contribution_pct_of_portfolio_delta": 0.08,
      "details": {
        "notes": "Unexplained residual (fees, timing, rounding)"
      }
    }
  ],
  "warnings": [],
  "stats": {
    "holdings_A": 5,
    "holdings_B": 6,
    "matched": 4,
    "added": 2,
    "removed": 1,
    "missing_market_values_count": 0
  }
}
```

## Git Ignore

**This directory is git-ignored** (except this README.md) because reports contain:
- Portfolio composition details
- Position sizes and changes
- Trading activity

- ✓ README.md is tracked
- ✗ All timestamped subdirectories are ignored
- ✗ All .json and .md reports are ignored

## Usage

### Basic Explanation
```bash
./bin/investos explain \
  --from portfolio/snapshots/2024-01-15-120000.json \
  --to portfolio/snapshots/2024-01-22-120000.json
```

### With Markdown Summary
```bash
./bin/investos explain \
  --from portfolio/snapshots/2024-01-15-120000.json \
  --to portfolio/snapshots/2024-01-22-120000.json \
  --format both
```

### Strict Mode (Fail on Missing Data)
```bash
./bin/investos explain \
  --from snapshot_A.json \
  --to snapshot_B.json \
  --strict
```

## Determinism and Reproducibility

Given identical input snapshots, the explain engine produces:
- ✓ Identical numeric attributions
- ✓ Identical driver classifications
- ✓ Identical warnings

Only these vary between runs:
- Report ID (timestamp-based)
- Generated timestamp
- Output directory path

## Use Cases

1. **Weekly Reviews**: Compare last week's snapshot to this week's to understand portfolio changes
2. **Transaction Verification**: Confirm buys/sells appear correctly in attribution
3. **Price Tracking**: Identify which holdings drove value changes
4. **Cash Flow Analysis**: Track deposits, withdrawals, and dividends via cash_change
5. **Data Quality**: Use residual_unexplained to spot data inconsistencies

## Limitations

- **No intraday data**: Cannot separate same-day price vs quantity effects
- **No cost basis**: Doesn't show realized gains/losses
- **No news/reasons**: Explains WHAT changed, not WHY (market reasons)
- **Snapshot-based only**: Cannot explain continuous movements between snapshots
- **Currency simplification**: FX effects only computed if explicitly tracked in snapshots

## Integration with Monitoring

Future steps will integrate explanations with:
- **Step 7**: Monitoring rules and daily digests
- **Step 8**: Investor lenses for deeper analysis
- **Step 9**: Automated playbooks for common scenarios

For now, explanations are run manually on-demand to understand portfolio changes.
