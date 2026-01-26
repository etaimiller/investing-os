# Fixtures Directory

This directory contains sample data files for testing and documentation purposes.

## Important Notice

**ALL DATA IN THIS DIRECTORY IS FICTIONAL**

- ISINs are fake (e.g., US0000000001, IE00B0000000)
- Ticker symbols are fictional (SMPL, SWLD, SMFG)
- Company names are invented (Sample Technology Corp, etc.)
- Values and prices are not real
- Do NOT use this data for actual investment decisions

## Purpose

Fixtures serve multiple purposes:

1. **Testing**: Enable unit and integration tests without real portfolio data
2. **Documentation**: Provide concrete examples of data structures
3. **Schema Validation**: Demonstrate schema-compliant data formats
4. **Development**: Allow development and testing without sensitive information

## Files

### sample_snapshot.json
A complete portfolio snapshot following `schema/portfolio-state.schema.json`.

**Contents**:
- 3 fictional holdings (2 stocks, 1 ETF)
- EUR 2,500 cash position
- Complete cost basis and market data
- Portfolio totals and allocation

**Usage**:
```bash
# Validate against schema
./bin/investos validate --file fixtures/sample_snapshot.json \
                        --schema schema/portfolio-state.schema.json

# Use in tests
python3 -m unittest tests/test_ingest.py
```

### sample_watch_rules.yaml (optional)
Sample monitoring rules configuration for testing.

## Adding New Fixtures

When creating new fixture data:

1. **Mark as fictional**: Include clear notices in metadata
2. **Use fake identifiers**: 
   - ISINs: Use patterns like US0000000001, IE00B0000000, DE0000000000
   - Tickers: Use obvious fakes like SMPL, TEST, FAKE
   - Names: Prefix with "Sample" or "Test"
3. **Follow schemas**: Ensure fixtures validate against schemas
4. **No real data**: Never include actual portfolio information
5. **Document purpose**: Explain what the fixture demonstrates

## Schema Compliance

All JSON fixtures should validate against their respective schemas:

```bash
# Portfolio snapshot
./bin/investos validate --file fixtures/sample_snapshot.json \
                        --schema schema/portfolio-state.schema.json

# Run all validation tests
python3 -m unittest discover tests -v
```

## Do NOT Commit

The following should NEVER be committed:
- Real portfolio data
- Actual broker PDFs
- Personal financial information
- Real ISINs with actual holdings
- Genuine account numbers or identifiers

If you accidentally commit sensitive data, immediately:
1. Remove it from the repository
2. Rewrite git history if necessary
3. Rotate any exposed credentials
4. Review git history for other exposures
