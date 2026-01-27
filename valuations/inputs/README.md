# Valuation Inputs Directory

This directory contains **user-provided fundamental data** for individual securities requiring valuation analysis.

## Purpose

Stock valuations require fundamental financial data (earnings, cash flow, balance sheet metrics) that cannot be automatically fetched. Users manually create JSON input files here with the required fundamentals for each security.

## File Naming Convention

- **Format**: `<ISIN>.json` or `<TICKER>.json`
- **Example**: `US0378331005.json` (Apple Inc.)

## Input File Structure

Each input file should contain:

```json
{
  "security_id": "US0378331005",
  "security_name": "Apple Inc.",
  "data_as_of_date": "2024-12-31",
  "currency": "USD",
  "fundamentals": {
    "revenue": {
      "current_ttm": 385000000000,
      "historical_5y": [[2020, 274515], [2021, 365817], ...]
    },
    "earnings": {
      "net_income_ttm": 97000000000,
      "historical_5y": [...]
    },
    "cash_flow": {
      "fcf_ttm": 110000000000,
      "historical_5y": [...]
    },
    "balance_sheet": {
      "total_debt": 106000000000,
      "cash_and_equivalents": 30000000000,
      "shareholders_equity": 62000000000,
      "shares_outstanding": 15550000000
    },
    "margins": {
      "operating_margin": 0.30,
      "net_margin": 0.25
    }
  },
  "sources": {
    "data_provider": "Annual Report 10-K",
    "links": ["https://investor.apple.com/..."],
    "notes": "FY2024 data"
  }
}
```

## Scaffold Generation

If you run valuation without input files, the system can generate scaffolds:

```bash
./bin/investos value --snapshot portfolio/latest.json --emit-scaffolds
```

This creates template files with `TODO` placeholders for you to fill in.

## Git Ignore

**This directory is git-ignored** (except this README.md) because input files may contain proprietary research or sensitive financial analysis.

- ✓ README.md is tracked
- ✗ All .json files are ignored
- ✗ All other files are ignored

If you want to commit sanitized example inputs for testing, explicitly add them:
```bash
git add -f valuations/inputs/example.json
```

## Data Sources

Recommended sources for fundamental data:
- Company annual reports (10-K, 20-F)
- Quarterly earnings releases (10-Q)
- Company investor relations websites
- Financial databases (if you have access)

## Quality Standards

- Use trailing twelve months (TTM) for current metrics
- Include 5-year historical data when available
- Document all data sources with dates and links
- Prefer conservative assumptions when estimates are needed
- Never fabricate data - mark as null if unavailable
