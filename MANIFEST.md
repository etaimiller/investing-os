# Investment OS Manifest

## Directory Structure Overview

This document serves as a navigation guide for the Investment OS, explaining the purpose and relationships of all files and directories.

## Root Files

### Constitutional Documents
- **`agents.md`** - Agent capabilities, constraints, and operating principles
- **`README.md`** - Project philosophy, architecture, and build roadmap
- **`MANIFEST.md`** - This file - navigation and structure guide
- **`.gitignore`** - Files to exclude from version control (sensitive data, temp files)

## Core Directories (Planned)

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

### `schema/` - Data Schemas (Planned for Step 2)
**Purpose**: JSON schemas for data validation and structure definitions

**Planned Structure**:
```
schema/
├── portfolio-snapshot.json
├── valuation-model.json
├── assumptions.json
└── decision-memo.json
```

**Status**: Not yet created

### `data/` - Portfolio Data (Planned for Step 4)
**Purpose**: All portfolio-related data files

**Planned Structure**:
```
data/
├── raw/                    # Trade Republic CSV exports
├── snapshots/              # Normalized portfolio snapshots
├── valuations/             # Security valuation analyses
├── assumptions/            # Per-security and per-analysis assumptions
├── decisions/              # Decision memos and rationale
└── monitoring/             # Daily digests and alerts
```

**Status**: Not yet created

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

### Step 1: Ontology-First Directory Skeleton
- **Dependencies**: Step 0 completion
- **Creates**: Full directory structure, empty placeholder files
- **Output**: Navigable codebase with clear organization

### Step 2: Core Data Schemas
- **Dependencies**: Step 1 directory structure
- **Creates**: schema/ directory with JSON validation schemas
- **Output**: Data validation and structure definitions

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

## File Relationships

```
agents.md ──► All operations (constraints)
README.md ──► Project philosophy (guidance)
MANIFEST.md ─► This file (navigation)
skills/ ──► Capabilities (execution)
schema/ ──► Data validation (structure)
data/ ──► Portfolio state (content)
bin/ ───► Interface (access)
```