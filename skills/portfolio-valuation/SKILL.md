---
name: portfolio-valuation
description: |
  Run deterministic, offline valuations on portfolio holdings using conservative
  assumptions. This skill classifies securities (stock/ETF/commodity), loads
  fundamental data when available, and produces per-holding valuation outputs.
  Valuations are reproducible and assumption-driven, never using external market data.
allowed_tools:
  - Makefile:value
  - Bash:./bin/investos value --snapshot <path>
  - Bash:ls valuations/inputs/*.json
  - Bash:ls valuations/outputs/*/
inputs:
  - snapshot: Path to portfolio snapshot (default: portfolio/latest.json)
  - profile: Assumption profile (default: conservative)
  - only_isin: Limit to single security (optional)
  - emit_scaffolds: Generate input templates for missing fundamentals
outputs:
  - valuation_outputs: Per-holding valuation JSON files
  - portfolio_summary: Aggregate portfolio-level analysis
  - input_scaffolds: Templates for missing fundamentals (if emit_scaffolds=true)
artifacts:
  - valuations/outputs/<timestamp>/<ISIN>-valuation.json: Per-holding analysis
  - valuations/outputs/<timestamp>/portfolio_summary.json: Portfolio aggregate
  - valuations/inputs/<ISIN>.json: User-provided fundamentals (optional input)
  - logs/runs/YYYY-MM-DD/HHMMSS_value.json: Run log
failure_modes:
  - snapshot_invalid: Snapshot doesn't validate against schema
  - missing_assumptions: assumptions/conservative.yaml not found
  - no_fundamentals: Stock lacks input file in valuations/inputs/
  - incomplete_valuation: Some fields calculable, others missing
examples:
  - "Value my portfolio"
  - "Run valuation analysis on holdings"
  - "Calculate intrinsic values for stocks"
---

# SKILL: portfolio-valuation

## WHEN TO USE THIS SKILL

Use this skill when:
- User asks to "value", "analyze", or "appraise" portfolio holdings
- User wants intrinsic value estimates
- User asks about margin of safety or valuation gaps
- User wants to identify over/undervalued positions
- User asks "what are my holdings worth?"

Do NOT use this skill when:
- User wants current market prices (use snapshots instead)
- User wants real-time quotes (not supported - offline only)
- User wants predictions (valuation is snapshot-in-time only)
- User wants trade recommendations (system doesn't provide these)

## PRECONDITIONS

**Required:**
- At least one portfolio snapshot exists
- `valuations/assumptions/conservative.yaml` exists
- Repository validated (run `make doctor` if uncertain)

**Optional but Recommended:**
- Fundamental data files in `valuations/inputs/<ISIN>.json`
- Without fundamentals, stocks get "incomplete" valuations

**Security Classification:**
- **Stocks:** Get full DCF valuation if fundamentals exist
- **ETFs:** Classified as allocation vehicles (no individual valuation)
- **Commodities:** Special handling (e.g., gold)

## STEP-BY-STEP PROCEDURE

### Step 1: Verify Snapshot Exists

```bash
ls -lh portfolio/latest.json
```

**Or use specific snapshot:**
```bash
ls -lh portfolio/snapshots/<snapshot_file>.json
```

### Step 2: Check Available Fundamentals (Optional)

```bash
ls valuations/inputs/*.json
```

**Expected:**
- JSON files named by ISIN (e.g., US0378331005.json)
- Each file contains earnings, growth rates, etc.

**If no files:**
- Valuation will run but stocks will be "incomplete"
- Can generate scaffolds with --emit-scaffolds

### Step 3: Run Valuation

**Using Makefile (PREFERRED):**
```bash
make value SNAPSHOT=portfolio/latest.json
```

**Using CLI directly:**
```bash
./bin/investos value --snapshot portfolio/latest.json
```

**With scaffold generation:**
```bash
./bin/investos value --snapshot portfolio/latest.json --emit-scaffolds
```

**For single security:**
```bash
./bin/investos value --snapshot portfolio/latest.json --only-isin US0378331005
```

**With custom profile:**
```bash
./bin/investos value --snapshot portfolio/latest.json --profile aggressive
```

### Step 4: Monitor Output

**Expected console output:**
```
Running valuation pipeline...
  Snapshot: portfolio/latest.json
  Profile: conservative

Validating snapshot against schema...
✓ Snapshot validated

✓ Valuation complete!

  Output directory: valuations/outputs/20260129_143530
  Holdings processed: 14

Status:
  Complete valuations: 5
  Incomplete valuations: 4
  Allocation vehicles: 5

Top 5 Holdings by Weight:
   20.5% - iShsIV-EO Ultrashort Bd U.ETF
   10.7% - iShs IV-iShs MSCI India UC.ETF
   10.1% - Fairfax Finl Holdings Ltd.
   10.1% - Berkshire Hathaway Inc.
    9.7% - InvescoMI S&P 500 ETF

Warnings (3):
  ⚠ US0378331005: No fundamentals file found
  ⚠ US5949181045: No fundamentals file found
  ⚠ US6541061031: No fundamentals file found
```

### Step 5: Review Valuation Outputs

```bash
ls -la valuations/outputs/<timestamp>/
```

**Expected files:**
- `<ISIN>-valuation.json` for each holding
- `portfolio_summary.json` for aggregate analysis

**Sample valuation file structure:**
```json
{
  "isin": "US0378331005",
  "name": "Apple Inc.",
  "classification": "stock",
  "valuation_status": "incomplete",
  "market_value": 45000.00,
  "intrinsic_value": null,
  "margin_of_safety": null,
  "warnings": ["No fundamentals data provided"]
}
```

### Step 6: Interpret Valuation Status

**Status Types:**

**complete:**
- Full valuation calculated
- Intrinsic value available
- Margin of safety computed

**incomplete:**
- Partial valuation only
- Missing fundamental data
- Stock needs input file

**allocation_vehicle:**
- ETF, index fund, or commodity
- Not individually valued
- Treated as portfolio allocation tool

## VERIFICATION & SUCCESS CRITERIA

Valuation succeeded if ALL of the following are true:

1. **Command exits with status 0**
2. **"✓ Valuation complete!" message appears**
3. **Output directory created** in valuations/outputs/
4. **Holdings processed count > 0**
5. **portfolio_summary.json exists**

## FAILURE HANDLING & RECOVERY

### Snapshot Invalid
**Symptom:** "✗ Snapshot validation FAILED"

**Recovery:**
1. Validate snapshot manually:
   ```bash
   ./bin/investos validate --file <snapshot> --schema schema/portfolio-state.schema.json
   ```
2. If invalid, re-ingest the PDF
3. Do not proceed with valuation

**Do NOT:**
- Attempt to fix snapshot
- Skip validation
- Use invalid snapshot

### Missing Assumptions File
**Symptom:** Error about "assumptions/conservative.yaml not found"

**Recovery:**
1. Check file exists:
   ```bash
   ls valuations/assumptions/conservative.yaml
   ```
2. If missing, repository is incomplete
3. Ask user: "Assumptions file missing. Re-clone repository?"

**Do NOT:**
- Create assumptions file
- Use different assumptions without user consent
- Proceed without assumptions

### No Fundamentals (Stocks)
**Symptom:** "⚠ <ISIN>: No fundamentals file found"

**Recovery:**
1. This is a WARNING, not an error
2. Valuation runs but stock marked "incomplete"
3. Inform user:
   ```
   Stock <NAME> needs fundamental data.
   Create valuations/inputs/<ISIN>.json
   Or run with --emit-scaffolds to generate template.
   ```
4. User must manually fill fundamental data

**Do NOT:**
- Fetch fundamentals from external APIs
- Invent earnings or growth rates
- Block valuation (incomplete is acceptable)

### Incomplete Valuation Output
**Symptom:** Valuation file has null intrinsic_value

**Recovery:**
1. Check valuation_status field
2. If "incomplete", fundamentals missing
3. If "allocation_vehicle", this is expected
4. Guide user to create input file:
   ```bash
   ./bin/investos value --snapshot portfolio/latest.json --emit-scaffolds
   ```

**Do NOT:**
- Treat incomplete as error
- Guess missing values
- Skip these holdings

## UNDERSTANDING VALUATION OUTPUTS

### Complete Valuation Structure

```json
{
  "isin": "US0378331005",
  "name": "Apple Inc.",
  "classification": "stock",
  "valuation_status": "complete",
  "market_value": 45000.00,
  "intrinsic_value": 52000.00,
  "margin_of_safety": 0.1346,
  "assumptions": {
    "discount_rate": 0.10,
    "terminal_growth": 0.03,
    "earnings_base": 95000000000,
    "growth_rate_5yr": 0.08
  },
  "warnings": []
}
```

### Interpreting Results

**margin_of_safety > 0:**
- Market price below intrinsic value
- Potential opportunity (if other factors favorable)

**margin_of_safety < 0:**
- Market price above intrinsic value
- Potentially overvalued

**margin_of_safety = null:**
- Incomplete valuation
- Need fundamental data

**valuation_status = "allocation_vehicle":**
- ETF or commodity
- No individual valuation (by design)

## CREATING FUNDAMENTAL INPUT FILES

### Step 1: Generate Scaffold

```bash
./bin/investos value --snapshot portfolio/latest.json --emit-scaffolds
```

**Creates:** `valuations/inputs/<ISIN>.json` templates

### Step 2: Fill Required Fields

Edit `valuations/inputs/<ISIN>.json`:

```json
{
  "isin": "US0378331005",
  "name": "Apple Inc.",
  "fundamentals": {
    "earnings_ttm": 95000000000,
    "revenue_ttm": 380000000000,
    "growth_rate_5yr": 0.08,
    "terminal_growth": 0.03,
    "discount_rate": 0.10
  },
  "source": "10-K 2023",
  "date": "2023-12-31"
}
```

### Step 3: Re-run Valuation

```bash
make value SNAPSHOT=portfolio/latest.json
```

**Expected:** Stock now shows "complete" status

## NOTES FOR AGENT REASONING

**Design Intent:**
Valuation is **deterministic and offline**. Same inputs always produce same outputs. No external data, no live prices, no APIs.

**Conservative Assumptions:**
- Default profile: "conservative"
- Higher discount rates
- Lower growth rates
- Margin of safety required

**What Gets Valued:**

**Stocks:**
- Individual company valuation
- DCF-based intrinsic value
- Requires fundamental data

**ETFs:**
- NOT individually valued
- Treated as allocation vehicles
- Portfolio-level analysis only

**Commodities:**
- Special handling (e.g., gold)
- No earnings-based valuation
- May use alternative methods

**Incomplete is Acceptable:**
Incomplete valuations are NORMAL and expected:
- User may not have fundamental data yet
- User may not want to value all holdings
- System never forces valuation
- Inform user, don't block

**Assumptions Are Explicit:**
Every valuation includes:
- Discount rate used
- Growth assumptions
- Terminal value assumptions
- Source of fundamentals

**No Recommendations:**
Valuation provides intrinsic value estimates, NOT:
- Buy/sell recommendations
- Price targets
- Trading signals
- Action items

**Reproducibility:**
Critical for audit trail:
- Same snapshot + same fundamentals + same assumptions = same valuation
- Timestamps excluded from reproducibility check
- UUIDs excluded from reproducibility check

**Composition with Other Skills:**

Typical workflow:
```
1. make summarize                    (understand current state)
2. make value SNAPSHOT=latest.json   (value holdings)
3. make ask Q="What looks undervalued?"  (interpret results)
4. make decide --isin <ISIN> --action add  (if considering purchase)
```

**Conservative Approach:**
- Missing data → report as incomplete
- No external fetching
- No guessing fundamentals
- Explicit assumptions always
- User provides all inputs

**Scaffold Generation:**
`--emit-scaffolds` creates templates:
- User must fill manually
- No pre-populated data
- Clear TODO markers
- Source attribution required
