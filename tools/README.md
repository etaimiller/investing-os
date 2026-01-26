# Tools Directory

This directory contains the Investment OS CLI and supporting utilities.

## Investment OS CLI (`investos`)

The `investos` CLI is the primary interface to the Investment OS. It provides a structured "syscall" interface for all repository operations.

### Installation

**Requirements**: Python 3.7+

The CLI uses Python's standard library only - no external dependencies required.

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

**Optional: Use virtual environment**:
```bash
# Create venv (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# CLI still works the same way
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
Validate JSON files:
```bash
# With schema validation
./bin/investos validate --file portfolio/snapshots/2024-01-15-143022.json \
                        --schema schema/portfolio-state.schema.json

# JSON syntax only (no schema)
./bin/investos validate --file valuations/inputs/AAPL.json
```

**Note**: Full JSON Schema Draft-07 validation will be enabled in Step 4/5 with jsonschema library. Currently performs basic structure validation.

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