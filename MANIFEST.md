# Investment OS Manifest

## Directory Structure Overview

This document serves as a navigation guide for the Investment OS, explaining the purpose and relationships of all files and directories.

## Root Files

### Constitutional Documents
- **`agents.md`** - Agent capabilities, constraints, and operating principles
- **`README.md`** - Project philosophy, architecture, and build roadmap
- **`MANIFEST.md`** - This file - navigation and structure guide
- **`.gitignore`** - Files to exclude from version control (sensitive data, temp files)

## Core Directories

### `skills/` - Agent Skills Framework
**Purpose**: Organized capabilities following the Agent Skills specification (agentskills.io)

**Structure**:
```
skills/
├── README.md           # Skills overview and framework guide
├── portfolio-ingestion/  # Transform raw data into snapshots
├── valuation/          # Conservative valuation models
├── monitoring/         # Portfolio tracking and alerts
└── analysis/           # Decision-making frameworks
```

**Status**: Empty placeholder with README (Step 0)

### `portfolio/` - Portfolio State and Holdings
**Purpose**: Current and historical portfolio state, holdings data, and account statements

**Three-layer architecture**:
- **Layer A**: Raw inputs (Trade Republic PDFs) in `raw/` - immutable source of truth
- **Layer B**: Canonical snapshots (schema-validated JSON) in `snapshots/` - single source for analysis
- **Layer C**: Convenience exports (CSV, MD) generated from canonical JSON

**Structure**:
```
portfolio/
├── README.md          # Portfolio directory overview and three-layer architecture
├── raw/              # Raw broker statements (primarily Trade Republic PDFs)
│   └── README.md     # Raw input format documentation
├── snapshots/         # Canonical normalized snapshots (JSON, schema-validated)
│   └── template_holdings_snapshot.csv  # CSV mapping aid / convenience format
├── holdings/          # Current and recent holdings data (planned)
├── cash/             # Cash and money market fund balances (planned)
└── statements/       # Processed account statements (planned)
```

**Status**: Directories created with READMEs (Step 1, enhanced Step 2.1)
**See**: 
- [portfolio/README.md](portfolio/README.md) for three-layer architecture details
- [portfolio/raw/README.md](portfolio/raw/README.md) for raw PDF input format

### `research/` - Investment Research and Analysis
**Purpose**: Company research, financial analysis, market research, and security analysis

**Structure**:
```
research/
├── README.md          # Research directory overview and frameworks
├── companies/         # Individual company research
├── industries/        # Industry analysis and trends
├── markets/          # Market research and conditions
├── financials/       # Financial statement analysis
└── sources/          # Research sources and references
```

**Status**: Directory created with README (Step 1)
**See**: [research/README.md](research/README.md) for research frameworks

### `valuations/` - Security Valuation Models
**Purpose**: Intrinsic value calculations, assumptions, margin of safety analysis

**Structure**:
```
valuations/
├── README.md          # Valuation directory overview and methodologies
├── models/           # Valuation calculations and models
├── assumptions/      # Underlying assumptions by security
├── history/         # Historical valuations for accuracy tracking
└── summaries/       # Valuation summaries and conclusions
```

**Status**: Directory created with README (Step 1)
**See**: [valuations/README.md](valuations/README.md) for valuation principles

### `decisions/` - Investment Decision Records
**Purpose**: Decision memos, trade plans, decision frameworks, and decision history

**Structure**:
```
decisions/
├── README.md          # Decision directory overview and frameworks
├── memos/            # Complete decision memos with full rationale
├── trade-plans/      # Trade execution plans (human execution only)
├── frameworks/       # Decision templates and checklists
└── history/         # Decision outcomes and performance tracking
```

**Status**: Directory created with README (Step 1)
**See**: [decisions/README.md](decisions/README.md) for decision framework

### `monitoring/` - Portfolio Monitoring and Alerts
**Purpose**: Monitoring rules, daily digests, alert configurations, performance tracking

**Structure**:
```
monitoring/
├── README.md          # Monitoring directory overview and rules
├── rules/            # Monitoring rules and configurations
├── digests/          # Daily portfolio digests
├── alerts/           # Alert history and configurations
└── performance/      # Performance tracking and analysis
```

**Status**: Directory created with README (Step 1)
**See**: [monitoring/README.md](monitoring/README.md) for monitoring frameworks

### `playbooks/` - Operational Playbooks and Procedures
**Purpose**: Operational playbooks, troubleshooting guides, standard procedures

**Structure**:
```
playbooks/
├── README.md          # Playbooks directory overview and templates
├── operations/       # Operational playbooks and procedures
├── troubleshooting/  # Problem-solving guides and solutions
├── maintenance/      # System maintenance and update procedures
└── quality/         # Quality assurance and validation procedures
```

**Status**: Directory created with README (Step 1)
**See**: [playbooks/README.md](playbooks/README.md) for operational guides

### `logs/` - System Logs and Audit Trails
**Purpose**: System logs, operation records, audit trails, error logs

**Structure**:
```
logs/
├── README.md          # Logs directory overview and retention policies
├── system/           # System operation and health logs
├── operations/       # Data processing and analysis operation logs
├── audit/            # Complete audit trail of all actions
└── errors/          # Error records and troubleshooting logs
```

**Status**: Directory created with README (Step 1)
**See**: [logs/README.md](logs/README.md) for log management policies

### `tools/` - Standalone Tools and Utilities
**Purpose**: Data processing tools, analysis helpers, system utilities, validation tools

**Structure**:
```
tools/
├── README.md          # Tools directory overview and guidelines
├── data-processing/  # Data transformation and validation tools
├── analysis/        # Analysis support and calculation helpers
├── system/          # System administration and maintenance utilities
├── validation/      # Data quality and consistency checkers
└── reporting/       # Report generation and data export tools
```

**Status**: Directory created with README (Step 1)
**See**: [tools/README.md](tools/README.md) for tool development guidelines

### `schema/` - Data Schemas
**Purpose**: JSON schemas for data validation and structure definitions

**Structure**:
```
schema/
├── README.md                      # Schema documentation and principles
├── portfolio-state.schema.json   # Portfolio snapshot structure
├── valuation-model.schema.json   # Valuation analysis structure
└── decision-memo.schema.json     # Investment decision structure
```

**Status**: Created in Step 2
**See**: [schema/README.md](schema/README.md) for schema design principles

**Key Principles**:
- Separates facts, assumptions, and derived values
- Conservative validation rules
- Complete audit trail support
- All schemas versioned for compatibility

### `bin/` - CLI Tools (Planned for Step 3)
**Purpose**: Command-line interface and specialized scripts

**Planned Structure**:
```
bin/
├── investos               # Main CLI dispatcher
├── ingest                 # Portfolio ingestion script
├── value                  # Valuation analysis script
├── monitor                # Monitoring script
└── analyze                # Decision analysis script
```

**Status**: Not yet created

## Build Step Dependencies

### Step 0: Repository Constitution ✓
- **Files Created**: agents.md, README.md, .gitignore, MANIFEST.md, skills/README.md
- **Dependencies**: None
- **Output**: Constitutional foundation and guardrails

### Step 1: Ontology-First Directory Skeleton ✓
- **Dependencies**: Step 0 completion
- **Creates**: Full directory structure with README files
- **Directories Created**: portfolio/, research/, valuations/, decisions/, monitoring/, playbooks/, logs/, tools/
- **Output**: Navigable codebase with clear organization and workflow documentation

### Step 2: Core Data Schemas ✓
- **Dependencies**: Step 1 directory structure
- **Creates**: schema/ directory with JSON validation schemas, templates, and assumption files
- **Files Created**: 
  - schema/portfolio-state.schema.json
  - schema/valuation-model.schema.json
  - schema/decision-memo.schema.json
  - portfolio/snapshots/template_holdings_snapshot.csv
  - valuations/assumptions/conservative.yaml
  - monitoring/watch_rules.yaml
- **Output**: Complete data format specifications separating facts, assumptions, and derived values

### Step 2.1: Tighten Snapshot Contract and PDF Input ✓
- **Dependencies**: Step 2 schemas
- **Creates**: Raw input documentation and schema placement clarity
- **Files Created/Updated**:
  - portfolio/raw/README.md (Trade Republic PDF as primary input)
  - Updated portfolio/README.md (three-layer architecture: raw PDFs → canonical JSON → convenience exports)
  - Updated portfolio/snapshots/template_holdings_snapshot.csv (clarify CSV is convenience format)
  - Updated schema/README.md (centralized schema approach documented)
  - Updated monitoring/watch_rules.yaml (alert noise controls: cooldown, digest limits, snooze)
  - Updated valuations/assumptions/conservative.yaml (per-asset-class overrides, profiles)
- **Output**: Clear separation of raw PDFs, canonical JSON, and convenience formats; enhanced monitoring and assumption flexibility

### Step 3: Dispatch-Style CLI Scaffold
- **Dependencies**: Step 2 schemas
- **Creates**: bin/ directory with CLI dispatcher and skill integration
- **Output**: Executable interface to the system

### Step 4: Portfolio Ingestion
- **Dependencies**: Step 3 CLI, Step 2 schemas
- **Creates**: data/ directory structure and ingestion skill
- **Output**: Functional data processing pipeline

### Step 5: Valuation v1
- **Dependencies**: Step 4 data pipeline
- **Creates**: Valuation models and analysis skills
- **Output**: Basic security valuation capability

### Step 6: Price-Move Explanation
- **Dependencies**: Step 5 valuation models
- **Creates**: Price analysis and explanation frameworks
- **Output**: Automated reasoning for portfolio changes

### Step 7: Monitoring Rules + Daily Digest
- **Dependencies**: Step 6 explanation system
- **Creates**: Monitoring skills and alert generation
- **Output**: Automated portfolio monitoring

### Step 8: Investor Lenses
- **Dependencies**: Step 7 monitoring
- **Creates**: Advanced analytical frameworks
- **Output**: Comprehensive decision-making tools

### Step 9: Verification Tooling + Playbooks
- **Dependencies**: All previous steps
- **Creates**: System health checks and troubleshooting guides
- **Output**: Complete, maintainable system

## File Naming Conventions

### Timestamps
- **Format**: YYYY-MM-DD-HHMMSS (e.g., 2024-01-15-143022)
- **Purpose**: Chronological ordering of snapshots and analyses
- **Usage**: portfolio-snapshots/, decisions/, monitoring/

### Identifiers
- **Securities**: Use ISIN or ticker symbol consistently
- **Analyses**: Combine security ID with timestamp
- **Assumptions**: Link to specific security or analysis

### Version Control
- **Immutable**: Never modify past files, always create new versions
- **Descriptive**: Commit messages explain what changed and why
- **Atomic**: Each commit represents one logical operation

## TODO Tracking

### Configuration Required
- TODO: Portfolio data storage location preferences
- TODO: Snapshot frequency requirements
- TODO: Valuation margin of safety thresholds
- TODO: Monitoring scope and metrics
- TODO: Daily digest content preferences

### Design Decisions Pending
- TODO: Finalize directory structure based on Step 1 feedback
- TODO: Confirm data schema requirements for Step 2
- TODO: Validate CLI approach for Step 3
- TODO: Review skill categories for Step 4+

## Navigation Tips

1. **Start with README.md** for project overview
2. **Consult agents.md** for operational constraints
3. **Reference MANIFEST.md** for structure guidance
4. **Check skills/** for available capabilities
5. **Follow step-by-step** build process in order

## Workflow Relationships

```
agents.md ──────► All operations (constraints)
README.md ──────► Project philosophy (guidance)
MANIFEST.md ────► This file (navigation)

skills/ ────────► Capabilities (execution)
portfolio/ ─────► Current state (holdings)
research/ ──────► Analysis input (company info)
valuations/ ────► Intrinsic value (pricing)
decisions/ ─────► Action records (audit)
monitoring/ ────► Ongoing tracking (alerts)
playbooks/ ─────► Procedures (operations)
logs/ ──────────► Audit trail (history)
tools/ ─────────► Utilities (helpers)

schema/ ────────► Data validation (structure) [Planned]
bin/ ───────────► Interface (access) [Planned]
```

## Investor Workflow Through Directories

1. **Portfolio State** → `portfolio/` - Current holdings and historical snapshots
2. **Research Phase** → `research/` - Company and market analysis
3. **Valuation** → `valuations/` - Intrinsic value calculations
4. **Decision Making** → `decisions/` - Investment decision records
5. **Ongoing Monitoring** → `monitoring/` - Daily digests and alerts
6. **Operations** → `playbooks/` - Standard procedures and troubleshooting
7. **Audit Trail** → `logs/` - Complete system operation history
8. **Utilities** → `tools/` - Standalone processing and analysis tools