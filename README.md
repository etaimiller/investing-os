# Investment OS

A file-based, agent-operated operating system for managing a personal investment portfolio.

## Philosophy

**Files are the source of truth.** This Investment OS stores all portfolio state, analysis, and decisions as versioned files. Chat interactions coordinate file-based work, but never replace it.

**Git provides the audit trail.** Every action, analysis, and decision is traceable through git history, creating a complete record of the investment process.

**Agents operate within constraints.** Specialized agents execute specific tasks while respecting strict safety boundaries and requiring human approval for all decisions.

## Core Principles

- **Reproducible analysis** - Every analysis can be repeated with the same inputs
- **Assumption-driven** - All valuations surface their underlying assumptions
- **Conservative by default** - When uncertain, choose the more conservative approach
- **Never executes trades** - The system provides analysis, never execution
- **Human approval required** - All decisions require explicit confirmation

## System Architecture

### Data Flow
```
Trade Republic CSV → Normalized Snapshots → Analysis → Decisions
```

### File-Based Storage
- **Portfolio snapshots** - Timestamped JSON files representing portfolio state
- **Valuation models** - Conservative intrinsic value calculations
- **Assumptions** - Tracked and versioned with analyses
- **Decision memos** - Complete rationale for investment decisions
- **Monitoring rules** - Automated alerts and daily digests

### Agent Skills Framework
The system uses the Agent Skills framework (agentskills.io) to organize capabilities:
- **Portfolio ingestion** - Transform raw data into normalized snapshots
- **Valuation analysis** - Apply conservative valuation frameworks
- **Monitoring rules** - Track changes and generate alerts
- **Investor lenses** - Apply analytical frameworks for decision-making

## Build Roadmap

This system is built incrementally through explicit steps:

### Step 0: Repository Constitution and Guardrails
- Define agent capabilities and constraints
- Establish file-based source of truth principles
- Create git workflow rules and audit requirements

### Step 1: Ontology-First Directory Skeleton
- Create directory structure based on data relationships
- Define file naming conventions and organization
- Establish MANIFEST for navigation

### Step 2: Core Data Schemas
- Define JSON schemas for portfolio snapshots
- Create assumption tracking structures
- Establish validation rules

### Step 3: Dispatch-Style CLI Scaffold
- Create main CLI dispatcher
- Implement agent skills integration
- Establish task automation framework

### Step 4: Portfolio Ingestion
- Transform Trade Republic CSV to normalized snapshots
- Implement data validation and consistency checks
- Create historical state tracking

### Step 5: Valuation v1
- Implement simple, conservative valuation models
- Create margin of safety calculations
- Establish reproducible analysis framework

### Step 6: Price-Move Explanation
- Offline-first price movement analysis
- Create explanation templates and frameworks
- Implement automated reasoning

### Step 7: Monitoring Rules + Daily Digest
- Define monitoring thresholds and rules
- Create automated daily digest generation
- Implement alert system

### Step 8: Investor Lenses
- Implement analytical frameworks for decision-making
- Create qualitative assessment tools
- Establish comprehensive analysis workflows

### Step 9: Verification Tooling + Playbooks
- Create system health checks and validation
- Implement troubleshooting playbooks
- Establish maintenance procedures

## Getting Started

### Prerequisites
- Git for version control
- A text editor for file-based work
- Trade Republic account for portfolio data export

### Initial Setup
1. Clone this repository
2. Review `agents.md` for operating constraints
3. Follow the step-by-step build process
4. Each step requires explicit authorization before proceeding

### Data Security
- Personal portfolio data is never exposed to external services
- All analysis happens offline-first
- Sensitive information is clearly marked and protected

## TODO: User Input Required

**Configuration:**
- TODO: Where should raw Trade Republic CSV files be stored?
- TODO: How often should portfolio snapshots be created?
- TODO: What minimum margin of safety should be required?

**Preferences:**
- TODO: Which metrics should be included in daily monitoring digests?
- TODO: What qualitative assessment frameworks should be prioritized?
- TODO: How should portfolio rebalancing recommendations be presented?

## Contributing

This is a personal investment system designed for individual use. All modifications should:
- Maintain the file-based source of truth principle
- Preserve git audit trail integrity
- Follow conservative, assumption-driven analysis
- Respect agent safety constraints

## License

This Investment OS is designed for personal portfolio management. All analysis and decision-making frameworks are provided for educational purposes.