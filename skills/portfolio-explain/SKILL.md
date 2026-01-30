---
name: portfolio-explain
description: |
  Explain mechanical portfolio changes between two snapshots using deterministic
  attribution. This skill decomposes portfolio value changes into drivers:
  price changes, quantity changes, new positions, removed positions, and cash changes.
  Use when user wants to understand what changed in their portfolio.
allowed_tools:
  - Makefile:explain
  - Bash:./bin/investos explain --from <snapshot_A> --to <snapshot_B>
  - Bash:ls portfolio/snapshots/*.json
inputs:
  - snapshot_A: Path to earlier snapshot (from state)
  - snapshot_B: Path to later snapshot (to state)
  - format: Output format (json/md/both, default: json)
outputs:
  - explanation_json: Machine-readable attribution report
  - explanation_md: Human-readable summary (if requested)
  - delta_total: Total portfolio value change
  - drivers: Ranked list of change contributors
artifacts:
  - monitoring/explanations/<timestamp>/explanation.json: Attribution report
  - monitoring/explanations/<timestamp>/explanation.md: Summary (if format=md or both)
  - logs/runs/YYYY-MM-DD/HHMMSS_explain.json: Run log
failure_modes:
  - snapshot_not_found: One or both snapshot files don't exist
  - snapshot_invalid: Snapshots don't validate against schema
  - missing_market_values: Holdings lack price data (handled as residual)
  - identical_snapshots: No changes detected between snapshots
examples:
  - "What changed in my portfolio since last week?"
  - "Explain the difference between yesterday and today"
  - "Why did my portfolio value increase?"
---

# SKILL: portfolio-explain

## WHEN TO USE THIS SKILL

Use this skill when:
- User asks "what changed?" or "why did portfolio value change?"
- User provides two dates or times to compare
- User mentions recent portfolio movements
- User wants to understand value attribution
- After ingesting new statement and wanting to compare to previous

Do NOT use this skill when:
- User asks about current state (use portfolio-qa instead)
- User wants valuation analysis (use portfolio-valuation instead)
- Only one snapshot exists
- User wants predictions or forecasts (explanation is historical only)

## PRECONDITIONS

**Required:**
- At least 2 portfolio snapshots must exist
- Snapshots must be valid JSON (schema-conformant)
- Snapshots must have market values for holdings

**Snapshot Selection:**
- Earlier snapshot is "from" (A)
- Later snapshot is "to" (B)
- Order matters: FROM must be before TO chronologically

## STEP-BY-STEP PROCEDURE

### Step 1: Identify Snapshots to Compare

**List available snapshots:**
```bash
ls -lt portfolio/snapshots/*.json | head -10
```

**Expected output shows:**
- Timestamped JSON files
- Most recent at top (if using -lt)

**Find specific date:**
```bash
ls portfolio/snapshots/2026-01-2*.json
```

**Typical pattern:**
- FROM: Older snapshot (e.g., last week)
- TO: Newer snapshot (e.g., today)

### Step 2: Verify Snapshot Paths

```bash
ls -lh portfolio/snapshots/<from_file>.json
ls -lh portfolio/snapshots/<to_file>.json
```

**Expected:**
- Both files exist
- Reasonable file sizes (5-50KB typically)

### Step 3: Run Explanation

**Using Makefile (PREFERRED):**
```bash
make explain FROM=portfolio/snapshots/<from_file>.json TO=portfolio/snapshots/<to_file>.json
```

**Using CLI directly:**
```bash
./bin/investos explain \
  --from portfolio/snapshots/<from_file>.json \
  --to portfolio/snapshots/<to_file>.json
```

**With markdown output:**
```bash
./bin/investos explain \
  --from portfolio/snapshots/2026-01-22-120000.json \
  --to portfolio/snapshots/2026-01-29-120000.json \
  --format both
```

**Example:**
```bash
make explain \
  FROM=portfolio/snapshots/2026-01-22-120000.json \
  TO=portfolio/snapshots/2026-01-29-143022.json
```

### Step 4: Read Output

**Expected console output:**
```
Explaining portfolio changes...
  From: 2026-01-22-120000.json
  To: 2026-01-29-143022.json
  Format: json

Validating snapshots...
✓ Both snapshots validated

✓ Explanation complete!

Portfolio Change:
  From: 159,234.50 EUR
  To:   193,666.76 EUR
  Δ:    +34,432.26 EUR (+21.62%)

Top 10 Drivers:
  price_change      Apple Inc.                  +12,500.00  (36.3%)
  quantity_change   S&P 500 ETF                 +8,000.00   (23.2%)
  new_position      Microsoft Corp.             +6,000.00   (17.4%)
  price_change      Berkshire Hathaway          +4,500.00   (13.1%)
  ...

Output directory: monitoring/explanations/20260129_143530
```

### Step 5: Locate Output Files

```bash
ls -la monitoring/explanations/*/
```

**Expected artifacts:**
- `explanation.json` - Machine-readable report
- `explanation.md` - Human summary (if requested)

### Step 6: Review Key Sections

**In explanation.json:**
- `totals`: Portfolio-level changes
- `drivers`: Ranked attribution
- `stats`: Counts (holdings, matched, added, removed)
- `warnings`: Data quality issues

## VERIFICATION & SUCCESS CRITERIA

Explanation succeeded if ALL of the following are true:

1. **Command exits with status 0**
2. **"✓ Explanation complete!" message appears**
3. **explanation.json exists in output directory**
4. **Delta matches sum of drivers** (within rounding)
5. **No critical errors in warnings section**

## FAILURE HANDLING & RECOVERY

### Snapshot Not Found
**Symptom:** "Error: Snapshot file not found"

**Recovery:**
1. List available snapshots: `ls portfolio/snapshots/*.json`
2. Verify paths are correct
3. Use absolute paths if relative paths fail
4. Ask user to confirm snapshot names

**Do NOT:**
- Guess snapshot locations
- Search entire filesystem
- Create missing snapshots

### Snapshot Invalid
**Symptom:** "✗ From snapshot validation FAILED" or "✗ To snapshot validation FAILED"

**Recovery:**
1. Note which snapshot is invalid
2. Try validating manually:
   ```bash
   ./bin/investos validate --file <snapshot> --schema schema/portfolio-state.schema.json
   ```
3. Inform user which snapshot is broken
4. Suggest re-ingesting that date's PDF

**Do NOT:**
- Attempt to fix broken snapshots
- Skip validation
- Proceed with explanation

### Missing Market Values
**Symptom:** "⚠ X holdings without market values"

**Recovery:**
1. This is a WARNING, explanation still runs
2. Missing values treated as residual_unexplained
3. Inform user that attribution may be incomplete
4. Note which holdings lack values (in warnings)

**Do NOT:**
- Fetch external prices
- Block explanation
- Invent market values

### Identical Snapshots
**Symptom:** "⚠ No changes detected" or "Δ: 0.00 EUR"

**Recovery:**
1. This is valid - portfolio didn't change
2. Report to user: "No changes between these dates"
3. Check if snapshots are actually the same file
4. Confirm user intended to compare these specific dates

**Do NOT:**
- Report as error
- Try different snapshots without asking

### Large Residual Unexplained
**Symptom:** Warning about high residual (>5% of delta)

**Recovery:**
1. This indicates data quality issues
2. Possible causes:
   - Missing market values
   - Currency conversions
   - Fees/costs
   - Timing differences
3. Inform user: "Attribution is incomplete. Check for missing data."
4. Explanation is still valid, just incomplete

**Do NOT:**
- Block explanation
- Adjust numbers to force reconciliation
- Hide residual

## DRIVER TYPES EXPLAINED

Explanation attributes changes to these categories:

**price_change:**
- Same holding, same quantity, different value
- Interpretation: Market price moved
- Example: "Apple stock price increased"

**quantity_change:**
- Same holding, different quantity
- Interpretation: Bought or sold shares
- Example: "Purchased 100 more shares of MSFT"

**new_position:**
- Holding exists in TO but not in FROM
- Interpretation: Opened new position
- Example: "Initiated position in Tesla"

**position_removed:**
- Holding exists in FROM but not in TO
- Interpretation: Closed position
- Example: "Sold entire Nike position"

**cash_change:**
- Cash balance changed
- Interpretation: Deposit, withdrawal, or cash from trades
- Example: "Cash increased by €5,000"

**residual_unexplained:**
- Difference not attributed to above
- Interpretation: Rounding, fees, missing data
- Example: Small differences (<1%)

## NOTES FOR AGENT REASONING

**Design Intent:**
Explanation is purely mechanical attribution. It answers "what changed" NOT "why it changed" (that requires external context).

**Deterministic:**
Given the same two snapshots, explanation produces identical output (excluding timestamps/IDs). This ensures reproducibility.

**No External Data:**
Explanation uses ONLY snapshot data. It does not:
- Fetch current prices
- Access market data
- Retrieve news or events
- Make assumptions about user intent

**Interpretation Guidelines:**

**Large price_change:**
- Normal for volatile securities
- Check if market moved significantly
- Not an error condition

**Large quantity_change:**
- User likely traded
- Check if intentional or unexpected

**Many new_position:**
- User diversifying or rebalancing
- Normal during portfolio buildout

**Many position_removed:**
- User concentrating or liquidating
- Check if intentional

**High residual:**
- Data quality issue
- Inform user, don't block

**Composition with Other Skills:**

Typical workflow:
```
1. make ingest PDF=<new_statement>     (create new snapshot)
2. make explain FROM=<old> TO=<new>    (understand changes)
3. make ask Q="What changed?"          (narrative interpretation)
```

**Output Artifacts:**

**explanation.json structure:**
```json
{
  "snapshot_A_id": "2026-01-22-120000",
  "snapshot_B_id": "2026-01-29-143022",
  "totals": {
    "from_total": 159234.50,
    "to_total": 193666.76,
    "delta_abs": 34432.26,
    "delta_pct": 0.2162
  },
  "drivers": [
    {
      "type": "price_change",
      "isin": "US0378331005",
      "name": "Apple Inc.",
      "contribution_abs": 12500.00,
      "contribution_pct_of_portfolio_delta": 0.363
    },
    ...
  ],
  "stats": {
    "holdings_A": 12,
    "holdings_B": 14,
    "matched": 11,
    "added": 3,
    "removed": 1
  },
  "warnings": []
}
```

**Conservative Interpretation:**
- Report facts (numbers, holdings)
- Avoid speculation about causes
- Distinguish mechanical changes from user intent
- Large changes are not errors
- Missing data is reported, not invented
