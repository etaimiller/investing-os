---
name: portfolio-ingest
description: |
  Ingest Trade Republic portfolio PDF statements into canonical JSON snapshots.
  This is the entry point for all portfolio data. Ingestion creates timestamped
  snapshots that are immutable and schema-validated. Use this skill when new
  portfolio statements arrive or when historical data needs to be loaded.
allowed_tools:
  - Makefile:ingest
  - Bash:./bin/investos ingest --pdf <path> --account <account>
  - Bash:ls portfolio/raw/*.pdf
  - Bash:ls portfolio/snapshots/*.json
inputs:
  - pdf_path: Absolute or relative path to Trade Republic PDF
  - account_name: Account identifier (default: main)
outputs:
  - snapshot_json: Timestamped canonical snapshot in portfolio/snapshots/
  - snapshot_csv: Convenience CSV export in portfolio/snapshots/
  - raw_pdf_copy: PDF copied to portfolio/raw/ with timestamp
  - latest_pointer: portfolio/latest.json symbolic link updated
artifacts:
  - portfolio/raw/YYYYMMDD_HHMMSS_<account>_portfolio.pdf: Raw PDF archive
  - portfolio/snapshots/YYYY-MM-DD-HHMMSS.json: Canonical snapshot
  - portfolio/snapshots/YYYY-MM-DD-HHMMSS.csv: Convenience export
  - portfolio/latest.json: Pointer to most recent snapshot
  - logs/runs/YYYY-MM-DD/HHMMSS_ingest.json: Structured run log
failure_modes:
  - pdf_not_found: PDF path does not exist or is not readable
  - pdf_parse_error: PDF structure doesn't match Trade Republic format
  - schema_validation_error: Extracted data doesn't conform to portfolio-state.schema.json
  - missing_market_values: Some holdings lack price data (logged as warning)
  - duplicate_snapshot: Snapshot with same timestamp already exists
examples:
  - "Ingest my new Trade Republic statement"
  - "Load portfolio data from PDF"
  - "Process the statement in ~/Downloads/portfolio.pdf"
---

# SKILL: portfolio-ingest

## WHEN TO USE THIS SKILL

Use this skill when:
- User provides a PDF file path or says they have a new statement
- User asks to "load", "import", "ingest", or "process" portfolio data
- User mentions Trade Republic, broker statement, or portfolio PDF
- User wants to update portfolio with latest positions

Do NOT use this skill when:
- User already has snapshots and wants to analyze them
- User asks about portfolio state without providing new data
- PDF is not from Trade Republic (system only supports TR format)
- User wants to manually edit portfolio data (not supported)

## PRECONDITIONS

**Required:**
- Trade Republic PDF file must exist and be readable
- PDF must be digital (not scanned - OCR not supported)
- Repository must have valid directory structure (run `make doctor` if uncertain)

**File Location:**
- PDF can be anywhere accessible (Downloads, Desktop, etc.)
- Will be copied to `portfolio/raw/` during ingestion

**Account Name:**
- Optional parameter (defaults to "main")
- Use distinct names for multiple accounts (e.g., "main", "retirement", "spouse")

## STEP-BY-STEP PROCEDURE

### Step 1: Verify PDF Exists

```bash
ls -lh <pdf_path>
```

**Expected:** File exists and has reasonable size (typically 50KB-5MB)

**If file not found:**
- Ask user for correct path
- Suggest: `ls ~/Downloads/*.pdf` to find recent PDFs

### Step 2: Run Ingestion Command

**Using Makefile (PREFERRED):**
```bash
make ingest PDF=<path> ACCOUNT=<account_name>
```

**Using CLI directly:**
```bash
./bin/investos ingest --pdf <path> --account <account_name>
```

**Examples:**
```bash
# Default account
make ingest PDF=~/Downloads/statement.pdf

# Named account
make ingest PDF=~/Downloads/statement.pdf ACCOUNT=main

# Full CLI with options
./bin/investos ingest --pdf ~/Downloads/portfolio_20260129.pdf --account main
```

### Step 3: Monitor Output

**Expected output includes:**
- "✓ Ingestion complete!"
- Snapshot path (portfolio/snapshots/YYYY-MM-DD-HHMMSS.json)
- Holdings extracted count
- Any warnings about missing data

**Example successful output:**
```
Ingesting Trade Republic PDF...
  Source: /Users/user/Downloads/statement.pdf
  Account: main

✓ Ingestion complete!

  Raw PDF: portfolio/raw/20260129_143022_main_portfolio.pdf
  Snapshot: portfolio/snapshots/2026-01-29-143022.json
  Latest: portfolio/latest.json
  CSV export: portfolio/snapshots/2026-01-29-143022.csv

  Holdings extracted: 14

Run log: logs/runs/2026-01-29/143022_ingest.json
```

### Step 4: Verify Snapshot Created

```bash
ls -lh portfolio/snapshots/*.json | tail -5
```

**Expected:**
- New JSON file with current timestamp
- File size typically 5-50KB depending on holdings count
- `portfolio/latest.json` points to new snapshot

### Step 5: Validate Snapshot (Optional but Recommended)

```bash
./bin/investos validate --file portfolio/latest.json --schema schema/portfolio-state.schema.json
```

**Expected:** "Validation passed"

## VERIFICATION & SUCCESS CRITERIA

Ingestion succeeded if ALL of the following are true:

1. **Command exits with status 0** (no error)
2. **New snapshot exists:** `portfolio/snapshots/YYYY-MM-DD-HHMMSS.json`
3. **Holdings count > 0** (unless portfolio is empty)
4. **Latest pointer updated:** `portfolio/latest.json` points to new snapshot
5. **Run log created:** `logs/runs/YYYY-MM-DD/HHMMSS_ingest.json` exists

## FAILURE HANDLING & RECOVERY

### PDF Not Found
**Symptom:** Error: "PDF path does not exist"

**Recovery:**
1. Ask user to verify path: `ls <path>`
2. Check common locations: `ls ~/Downloads/*.pdf`
3. Ask user to provide correct path

**Do NOT:**
- Guess or invent paths
- Search the entire filesystem
- Assume PDF location

### PDF Parse Error
**Symptom:** Error mentions "PDF structure", "extraction failed", or "format mismatch"

**Recovery:**
1. Verify PDF is from Trade Republic (not other broker)
2. Check PDF is digital (not scanned image)
3. Ask user if this is a Trade Republic PDF
4. If yes, report: "PDF format may have changed. Manual review needed."

**Do NOT:**
- Attempt to parse non-Trade-Republic PDFs
- Modify PDF structure
- Retry with different parsers

### Schema Validation Error
**Symptom:** Error: "Snapshot validation FAILED" with field-level errors

**Recovery:**
1. This indicates a bug in the ingestion logic
2. Report the error to user
3. Snapshot is still created but may be malformed
4. Suggest: Review snapshot manually or report issue

**Do NOT:**
- Modify snapshot to "fix" validation
- Retry ingestion automatically

### Missing Market Values (Warning)
**Symptom:** "Warnings: X holdings without market values"

**Recovery:**
1. This is a WARNING, not an error
2. Ingestion succeeded
3. Inform user that some positions lack price data
4. This is normal for certain security types (e.g., cash, pending trades)

**Do NOT:**
- Treat warnings as failures
- Attempt to fetch missing prices
- Block ingestion

### Duplicate Snapshot
**Symptom:** Snapshot with same timestamp already exists

**Recovery:**
1. Wait 1 second and retry (timestamps have second precision)
2. Or ask user if they want to overwrite
3. Or suggest using different account name

**Do NOT:**
- Automatically overwrite
- Silently skip ingestion

## NOTES FOR AGENT REASONING

**Design Intent:**
Ingestion is the **only** way portfolio data enters the system. It creates immutable, timestamped snapshots that serve as the source of truth for all downstream analysis.

**Trade Republic Format:**
The system is specifically designed for Trade Republic PDFs. These contain:
- Holdings table with ISIN, quantity, prices, market values
- Cash positions
- Account metadata
- Extraction uses column reconstruction (not text search)

**Deterministic Output:**
Given the same PDF, ingestion produces identical JSON (excluding timestamps and UUIDs). This is critical for reproducibility.

**Snapshots Are Immutable:**
Once created, snapshots should never be modified. If data is wrong:
- Re-ingest the PDF (creates new snapshot)
- Or manually correct the PDF and re-ingest

**What Gets Written to Disk:**
- **portfolio/raw/:** Original PDF (with timestamp prefix)
- **portfolio/snapshots/:** JSON snapshot + CSV export
- **portfolio/latest.json:** Symlink to most recent
- **logs/runs/:** Structured log with extraction details

**Schema Validation:**
All snapshots are validated against `schema/portfolio-state.schema.json`. This ensures:
- Required fields present
- Correct data types
- Holdings have ISINs
- Totals reconcile

**Next Steps After Ingestion:**
Typically follow ingestion with:
1. `make summarize` - Create queryable state
2. `make ask Q="What changed?"` - Understand updates
3. `make explain FROM=<old> TO=<new>` - Analyze deltas

**CSV Export:**
A convenience CSV is generated alongside JSON. It's useful for:
- Quick inspection in spreadsheet tools
- Human review of holdings
- But JSON is the canonical format

**Conservative Approach:**
- Never guess missing data
- Never fetch external prices
- Never modify user's PDF
- Always preserve original PDF in portfolio/raw/
- Warnings are acceptable; errors mean stop
