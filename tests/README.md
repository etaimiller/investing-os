# Tests Directory

This directory contains tests for Investment OS components.

## Test Structure

```
tests/
├── test_ingest.py          # PDF ingestion tests
├── test_validate.py        # Validation tests  
├── test_doctor.py          # Health check tests
└── fixtures/               # Test fixtures (sample data, NOT real PDFs)
    └── sample_parsed_data.json
```

## Running Tests

Tests use Python's stdlib unittest module:

```bash
# Run all tests
python3 -m unittest discover tests

# Run specific test file
python3 -m unittest tests/test_ingest.py
```

## Test Fixtures

**IMPORTANT**: Do NOT commit real Trade Republic PDFs or personal financial data.

Test fixtures should contain:
- Mocked parsed data structures
- Synthetic test data
- Sample JSON structures

Real PDFs for manual testing should be kept outside the repository.

## Writing Tests

Tests should:
- Use stdlib unittest module
- Mock external dependencies where possible
- Test contract adherence (schema compliance)
- Verify error handling
- Check data validation logic
