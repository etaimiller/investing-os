# Tools Directory

This directory contains the Investment OS CLI and supporting utilities.

## Investment OS CLI (`investos`)

The `investos` CLI is the primary interface to the Investment OS. It provides a structured "syscall" interface for all repository operations.

### Installation

**Requirements**: Python 3.7+

**Dependencies**:
- **Core CLI** (Step 3): Python stdlib only
- **PDF Ingestion** (Step 4): PyMuPDF for PDF text extraction
- **Schema Validation & Valuation** (Step 5): jsonschema, PyYAML

**Installation**:
```bash
# Install all dependencies (recommended method)
python3 -m pip install -r requirements.txt

# Or install manually
python3 -m pip install PyMuPDF~=1.23 jsonschema~=4.17 PyYAML~=6.0
```

**From repository root**:
```bash
# Make CLI executable (already done if you cloned repo)
chmod +x bin/investos

# Run from repo root
./bin/investos --help

# Or add to PATH for convenience
export PATH="$PATH:$(pwd)/bin"
investos --help
```

**Recommended: Use virtual environment**:
```bash
# Create venv (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
python3 -m pip install -r requirements.txt

# CLI now has full functionality
./bin/investos --help
```

### Available Commands

#### `investos status`
Show repository status:
- Latest portfolio snapshot
- Raw PDF count
- Last run log

```bash
./bin/investos status
```

#### `investos doctor`
Run health checks:
- Verify directory structure
- Check required files exist
- Validate JSON schemas
- Check portfolio snapshots

```bash
./bin/investos doctor
```

#### `investos validate`
Validate JSON files against schemas:
```bash
# Validate portfolio snapshot
./bin/investos validate --file portfolio/latest.json \
                        --schema schema/portfolio-state.schema.json

# Validate valuation output
./bin/investos validate --file valuations/outputs/20240127_143022/US0378331005-valuation.json \
                        --schema schema/valuation-model.schema.json

# JSON syntax only (no schema)
./bin/investos validate --file valuations/inputs/US0378331005.json
```

**Note**: Uses JSON Schema Draft-07 validation via jsonschema library (Step 5). Reports precise error paths for debugging.

#### `investos scaffold decision`
Create decision memo template:
```bash
./bin/investos scaffold decision --ticker AAPL
# Creates: decisions/2024-01-15_AAPL_decision.md
```

#### `investos scaffold valuation`
Create valuation input template:
```bash
./bin/investos scaffold valuation --ticker AAPL
# Creates: valuations/inputs/AAPL.json
```

#### `investos scaffold dossier`
Create research dossier:
```bash
./bin/investos scaffold dossier --ticker AAPL
# Creates: research/AAPL/dossier.md
#          research/AAPL/README.md
```

#### `investos value`
Run valuation analysis on portfolio holdings:
```bash
# Value all holdings in latest snapshot
./bin/investos value --snapshot portfolio/latest.json

# Use specific profile and snapshot
./bin/investos value --snapshot tests/fixtures/snapshot_minimal.json --profile conservative

# Value single holding by ISIN
./bin/investos value --snapshot portfolio/latest.json --only-isin US0378331005

# Generate input scaffolds for missing fundamentals
./bin/investos value --snapshot portfolio/latest.json --emit-scaffolds
```

**What it does**:
1. Validates snapshot against schema
2. Classifies securities (stock/ETF/commodity)
3. Loads valuation assumptions from YAML profile
4. For stocks: checks for fundamental inputs in `valuations/inputs/<ISIN>.json`
5. Generates per-holding valuation outputs
6. Creates portfolio summary with position sizing and concentration analysis
7. Outputs written to timestamped directory: `valuations/outputs/<timestamp>/`

**Outputs**:
- `valuations/outputs/<timestamp>/<ISIN>-valuation.json` - Per-holding analysis
- `valuations/outputs/<timestamp>/portfolio_summary.json` - Portfolio-level summary

**Optional Inputs**:
- `valuations/inputs/<ISIN>.json` - User-provided fundamental data for stocks
- `valuations/assumptions/conservative.yaml` - Valuation assumptions profile

**Deterministic**: Same inputs always produce identical valuation results (excluding timestamps/IDs).

#### `investos explain`
Explain portfolio changes between two snapshots:
```bash
# Basic explanation
./bin/investos explain \
  --from portfolio/snapshots/2024-01-15-120000.json \
  --to portfolio/snapshots/2024-01-22-120000.json

# With markdown summary
./bin/investos explain \
  --from tests/fixtures/snapshot_A.json \
  --to tests/fixtures/snapshot_B.json \
  --format both

# Strict mode (fail on missing data)
./bin/investos explain --from A.json --to B.json --strict
```

**What it does**:
1. Validates both snapshots against schema
2. Computes portfolio delta (total value change)
3. Attributes change to mechanical drivers:
   - `price_change`: Same quantity, different value (price moved)
   - `quantity_change`: Bought or sold shares
   - `new_position`: Opened new holding
   - `position_removed`: Closed existing holding
   - `cash_change`: Cash balance changed
   - `residual_unexplained`: Rounding, fees, timing differences
4. Outputs deterministic JSON attribution report

**Outputs**:
- `monitoring/explanations/<timestamp>/explanation.json` - Machine-readable report
- `monitoring/explanations/<timestamp>/explanation.md` - Optional human summary

**Note**: This is NOT market commentary or news analysis. It's pure mechanical attribution: "What changed?" not "Why did it change?"

**Deterministic**: Same inputs produce identical attribution (excluding timestamps/report IDs).

#### `investos summarize`
Create portfolio state summary from latest snapshot:
```bash
./bin/investos summarize
```

**What it does**:
1. Loads most recent portfolio snapshot
2. Computes portfolio facts (totals, holdings, types, concentration)
3. Optionally includes recent changes from explanation files
4. Writes deterministic summary to `analysis/state/summary.json`

**Outputs**:
- `analysis/state/summary.json` - Structured portfolio facts
- `analysis/state/latest.json` - Pointer to latest snapshot

**Use this before**: Asking portfolio questions with `investos ask`

**Facts only**: No opinions, valuations, or assumptions. Just portfolio state.

#### `investos ask`
Ask questions about portfolio using investor lenses:
```bash
# General questions
./bin/investos ask "What should I pay attention to?"
./bin/investos ask "Where is my biggest risk?"

# Risk-focused (Marks lens)
./bin/investos ask "What would Howard Marks worry about?"
./bin/investos ask "Where could I lose money permanently?"

# Understanding-focused (Munger lens)  
./bin/investos ask "Do I really understand these businesses?"
./bin/investos ask "Where are my psychological blind spots?"

# Value-focused (Klarman lens)
./bin/investos ask "Where is my margin of safety?"
./bin/investos ask "Am I investing or speculating?"
```

**What it does**:
1. Loads portfolio summary from `analysis/state/summary.json`
2. Selects relevant investor lenses (Marks, Munger, Klarman)
3. Generates structured markdown analysis with:
   - Observations (facts from summary)
   - Risks to consider
   - Open questions
   - What deserves attention
4. Saves full analysis to `analysis/answers/<timestamp>_<slug>.md`
5. Prints summary to console

**Investor Lenses**:
- **Marks**: Risk, cycles, what's priced in, concentration
- **Munger**: Understanding, incentives, moats, psychology
- **Klarman**: Margin of safety, value discipline, catalysts

**No external data**: Works entirely from local portfolio snapshot. No APIs, no market data.

**See**: `analysis/README.md` for detailed documentation

#### `investos decide`
Create structured decision memos for portfolio actions:
```bash
# Review existing holding
./bin/investos decide --isin US0378331005

# Consider adding to position
./bin/investos decide --isin US0378331005 --action add

# Consider new position
./bin/investos decide --action new --name "Apple Inc." --isin US0378331005

# Consider trimming position
./bin/investos decide --isin IE00B4L5Y983 --action trim \
  --notes "Position grew to 20% via appreciation"

# Consider exiting
./bin/investos decide --isin US6541061031 --action exit

# Use specific lens
./bin/investos decide --isin US0846707026 --lens klarman

# Create template only (no analysis)
./bin/investos decide --isin US5949181045 --emit-template-only
```

**Actions:**
- `new` - Initiating new position
- `add` - Adding to existing position
- `trim` - Reducing position size
- `exit` - Closing position
- `hold` - Review current position (default)

**What it does**:
1. Loads portfolio snapshot and summary
2. Extracts position context (weight, concentration)
3. Applies investor lenses (Marks/Munger/Klarman)
4. Generates structured markdown memo with:
   - Decision framing (facts only)
   - Portfolio context
   - Lens-based analysis prompts
   - Disconfirming evidence section
   - Alternatives considered
   - Decision status checkboxes
   - Follow-up triggers

**Outputs**:
- `decisions/YYYY-MM-DD_<isin>_<action>.md` - Decision memo template

**Design principles**:
- No recommendations (structures thinking, doesn't decide)
- Facts vs. judgment clearly separated
- "Do nothing" as explicit choice
- All reasoning captured in durable files
- Never auto-executes trades

**See**: `decisions/README.md` for complete decision workflow

#### `investos ingest`
Ingest Trade Republic portfolio PDF:
```bash
./bin/investos ingest --pdf /path/to/trade_republic_portfolio.pdf --account main

# Without account name (defaults to "unknown")
./bin/investos ingest --pdf ~/Downloads/portfolio.pdf

# Skip CSV export
./bin/investos ingest --pdf portfolio.pdf --account retirement --no-csv
```

**What it does**:
1. Copies PDF to `portfolio/raw/` with proper naming convention
2. Extracts holdings data from PDF (name, ISIN, quantity, prices, values)
3. Creates canonical JSON snapshot in `portfolio/snapshots/`
4. Updates `portfolio/latest.json` pointer
5. Generates convenience CSV export in `portfolio/exports/` (unless --no-csv)
6. Writes structured run log

**Trade Republic PDF format expected**:
- Holdings table with: Name, ISIN, Quantity, Average Buy Price, Current Price, Current Value
- Cash position (optional)
- Digital PDF (not scanned - OCR not yet supported)

**Handling missing data**:
- Missing fields are set to null with warnings
- Incomplete data is logged but doesn't fail ingestion
- All warnings appear in snapshot metadata and run log

### Structured Logging

All CLI operations write structured JSON logs to `logs/runs/YYYY-MM-DD/HHMMSS_<command>.json`

**Log format**:
```json
{
  "timestamp": "2024-01-15T14:30:22Z",
  "command": "scaffold_decision",
  "args": ["--ticker", "AAPL"],
  "repo_root": "/path/to/investing-os",
  "paths_touched": ["decisions/2024-01-15_AAPL_decision.md"],
  "outcome": "success",
  "errors": [],
  "warnings": [],
  "info": {
    "ticker": "AAPL",
    "filepath": "decisions/2024-01-15_AAPL_decision.md"
  },
  "duration_ms": 45
}
```

Logs provide complete audit trail but **do NOT replace decision memos** - they're for system operations only.

### Configuration

CLI reads `config.json` at repository root. See `config.json` for settings:
- Timezone (default: Africa/Johannesburg)
- Base currency (default: EUR)
- Directory paths
- Default assumption files

## CLI Package Structure

```
tools/
├── investos/              # Python package
│   ├── __init__.py       # Package metadata
│   ├── cli.py            # Main CLI entrypoint
│   ├── config.py         # Configuration loader
│   ├── logging.py        # Structured logging
│   ├── doctor.py         # Health checks
│   ├── validate.py       # JSON validation
│   ├── scaffold.py       # Template scaffolding
│   └── utils.py          # Common utilities
└── README.md             # This file
```

## What Belongs Here

- **Investment OS CLI** - Primary system interface
- **Data processing tools** - Utilities for data transformation and validation
- **Analysis helpers** - Tools to support analysis workflows
- **System utilities** - Maintenance and administration tools
- **Validation tools** - Data quality and consistency checkers

## File Naming Convention

- **Processing tools**: `[function]-tool.rb` (e.g., `csv-validator-tool.rb`)
- **Analysis helpers**: `[task]-helper.rb` (e.g., `portfolio-analyzer-helper.rb`)
- **System utilities**: `[operation]-util.rb` (e.g., `backup-util.rb`)
- **Validation tools**: `[check]-validator.rb` (e.g., `data-validator.rb`)

## Tool Categories

1. **Data Processing** - CSV processing, data validation, transformation utilities
2. **Analysis Support** - Calculation helpers, report generators, formatters
3. **System Administration** - Backup tools, maintenance utilities, health checks
4. **Validation** - Data consistency checkers, schema validators
5. **Reporting** - Report generators, data exporters, visualization helpers

## Workflow Integration

1. **Standalone Execution** - Tools can be run independently for specific tasks
2. **Workflow Integration** - Tools can be integrated into larger workflows
3. **Skill Support** - Tools support Agent Skills execution
4. **Maintenance Operations** - Tools support system maintenance and updates

## When to Look Here

- **Specific tasks** - Use dedicated tools for focused operations
- **Data processing** - Process and validate data files
- **System maintenance** - Run maintenance and administrative tasks
- **Quality assurance** - Validate data and system integrity

## Directory Structure

```
tools/
├── data-processing/   # Data transformation and validation tools
├── analysis/         # Analysis support and calculation helpers
├── system/           # System administration and maintenance utilities
├── validation/       # Data quality and consistency checkers
└── reporting/        # Report generation and data export tools
```

## Tool Development Guidelines

**Modular Design:**
- Each tool should have a single, clear purpose
- Tools should be self-contained with minimal dependencies
- Clear input/output specifications
- Comprehensive error handling

**Documentation:**
- Each tool should include usage instructions and examples
- Document input requirements and output formats
- Include troubleshooting guidance for common issues
- Maintain changelog for tool updates

**Quality Assurance:**
- Tools should validate inputs and handle edge cases
- Include appropriate error messages and logging
- Test tools with various data scenarios
- Maintain tool performance and reliability

## Example Tool Structure

```ruby
#!/usr/bin/env ruby
# Tool Name: Brief description of what this tool does
# Usage: tool-name [options] [arguments]
# Purpose: How this tool fits into the workflow

# Required arguments
# Optional arguments with defaults
# Input validation and error handling
# Core functionality
# Output formatting and reporting
# Error handling and logging
```

## Tool Categories Examples

**Data Processing Tools:**
- CSV validation and cleaning
- Data format transformation
- Schema validation tools
- Data consistency checkers

**Analysis Support Tools:**
- Financial calculation helpers
- Portfolio analysis utilities
- Valuation model helpers
- Risk calculation tools

**System Utilities:**
- Backup and restore tools
- Data migration utilities
- System health checkers
- Performance monitoring tools

**Validation Tools:**
- Data schema validators
- Cross-referencing checkers
- Consistency verification tools
- Quality assurance utilities

## TODO: User Input Required

**Tool Priorities:**
- TODO: Which tools should be developed first for Step 3?
- TODO: What specific data processing utilities are needed?

**Integration Requirements:**
- TODO: How should tools integrate with Agent Skills?
- TODO: What input/output formats should tools support?

**Quality Standards:**
- TODO: What testing and validation procedures should tools follow?
- TODO: How should tool performance be measured and optimized?

## Notes

- Tools should be modular and reusable across different workflows
- Each tool should have clear documentation and usage examples
- Tools should handle errors gracefully and provide helpful feedback
- Maintain tool quality through testing and validation
- Tools support both manual execution and automated workflows
- Focus on tools that add unique value beyond existing Agent Skills