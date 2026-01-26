# Agents: Capabilities and Constraints

## Agent Operating Principles

This Investment OS is operated by agents with the following core principles:

### Source of Truth
- **Files are the source of truth** - All portfolio state, analysis, and decisions are stored in versioned files
- **Chat is for coordination** - Conversational interactions coordinate file-based work
- **Git provides audit trail** - Every action must be traceable via git history

### Analysis Requirements
- **Reproducible** - All analysis must be repeatable with the same inputs
- **Assumption-driven** - Every valuation and analysis must surface its assumptions
- **Separation of concerns** - Facts, assumptions, and opinions must be clearly distinguished
- **Conservative by default** - When uncertain, choose the more conservative approach

### Safety Constraints
- **NO TRADE EXECUTION** - The system NEVER executes trades under any circumstances
- **Human approval required** - All decisions require explicit human confirmation
- **No external APIs** - All data processing is offline-first unless explicitly authorized
- **Privacy first** - Personal portfolio data is never exposed to external services

## Git Workflow Rules

### Branch Strategy
- **Single main branch** - All work happens on the main branch
- **Chronological snapshots** - Portfolio states are timestamped and stored sequentially
- **No feature branches** - Analysis work is committed directly to maintain audit trail

### Commit Requirements
- **Atomic commits** - Each commit represents one logical operation
- **Descriptive messages** - Commit messages must explain what changed and why
- **Include analysis** - commits that change portfolio state must include supporting analysis

### File Organization
- **Immutable snapshots** - Past portfolio states are never modified
- **Clear naming** - Files use timestamp-based naming for chronological ordering
- **Assumptions tracked** - All assumptions are stored with the analyses that use them

## Agent Capabilities

### Authorized Actions
- **File analysis** - Read and analyze portfolio data, valuation files, and assumptions
- **Data processing** - Transform Trade Republic CSV into normalized JSON snapshots
- **Valuation modeling** - Create and maintain conservative valuation models
- **Report generation** - Generate analysis reports and monitoring digests
- **Skill execution** - Run specialized analysis skills using the Agent Skills framework

### Prohibited Actions
- **Trade execution** - Absolutely no buying, selling, or trade placement
- **External API calls** - No connections to brokerages, banks, or market data services
- **Secret handling** - No access to or storage of API keys, passwords, or credentials
- **Market timing** - No short-term trading recommendations or timing advice

## Agent Skills Framework

### Skill Categories
- **Portfolio Ingestion** - Transform raw data into normalized portfolio snapshots
- **Valuation Analysis** - Apply conservative valuation frameworks to securities
- **Monitoring Rules** - Track portfolio changes and generate alerts
- **Investor Lenses** - Apply analytical frameworks for decision-making

### Skill Execution
- **Skill discovery** - Agents automatically load relevant skills based on task context
- **Progressive disclosure** - Skills load instructions and resources as needed
- **Reproducible execution** - All skill runs are logged and auditable

## Decision-Making Framework

### Required Elements
Every investment decision or recommendation must include:
1. **Factual basis** - Current portfolio state and security information
2. **Assumptions** - Clear statement of all assumptions made
3. **Valuation analysis** - Conservative intrinsic value estimate with margin of safety
4. **Qualitative assessment** - Moat, management quality, capital allocation discipline
5. **Risk factors** - Specific risks and mitigating factors

### TODO: User Input Required

**Portfolio Data Management:**
- TODO: Where should raw Trade Republic CSV files be stored?
- TODO: How often should portfolio snapshots be created (daily, weekly, on-change)?

**Analysis Preferences:**
- TODO: What minimum margin of safety should be required for recommendations?
- TODO: Which metrics should be included in daily monitoring digests?
- TODO: What qualitative assessment frameworks should be prioritized?

**Monitoring Scope:**
- TODO: What price movement thresholds should trigger analysis?
- TODO: How should portfolio rebalancing recommendations be presented?

## Error Handling and Recovery

### Data Validation
- **Schema validation** - All JSON files must conform to defined schemas
- **Consistency checks** - Portfolio balances must reconcile with holdings
- **Cross-validation** - Multiple data sources when available

### Error Scenarios
- **Missing data** - Clearly mark assumptions when data is unavailable
- **Inconsistent data** - Flag conflicts and require human resolution
- **Valuation failures** - Fall back to more conservative approaches

## Compliance and Audit Trail

### Record Keeping
- **All analysis stored** - No ephemeral calculations or recommendations
- **Assumption versioning** - Changes to assumptions are tracked and versioned
- **Decision documentation** - Every decision has supporting analysis files

### Review Requirements
- **Periodic reviews** - Regular review of assumptions and valuation methods
- **Performance tracking** - Compare outcomes to original assumptions
- **Method updates** - Explicitly document changes to analysis methods