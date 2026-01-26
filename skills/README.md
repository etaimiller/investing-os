# Skills Directory

This directory contains Agent Skills - organized capabilities that agents can discover and use to perform specialized tasks within the Investment OS.

## Agent Skills Framework

This system follows the Agent Skills specification (agentskills.io). Each skill is a self-contained directory with:

- **`SKILL.md`** - Required skill definition with YAML frontmatter and instructions
- **`scripts/`** - Executable code for the skill
- **`references/`** - Additional documentation and resources
- **`assets/`** - Templates, schemas, and examples

## Planned Skill Categories

### Portfolio Ingestion
**Purpose**: Transform raw Trade Republic CSV data into normalized portfolio snapshots

**Capabilities**:
- CSV parsing and validation
- Data normalization and cleaning
- Snapshot creation with proper timestamps
- Consistency checking and error handling

### Valuation Analysis
**Purpose**: Apply conservative valuation frameworks to securities

**Capabilities**:
- Intrinsic value estimation (DCF-based)
- Relative valuation analysis
- Margin of safety calculations
- Qualitative assessment integration

### Monitoring Rules
**Purpose**: Track portfolio changes and generate automated alerts

**Capabilities**:
- Price movement monitoring
- Portfolio rebalancing alerts
- Daily digest generation
- Threshold-based notifications

### Analysis Frameworks
**Purpose**: Apply analytical frameworks for investment decision-making

**Capabilities**:
- Investor lens application
- Decision memo generation
- Risk assessment workflows
- Performance analysis

## Skill Structure

Each skill follows this standard structure:

```
skill-name/
├── SKILL.md              # Required: Skill definition and instructions
├── scripts/              # Executable code
│   └── main.rb          # Main skill execution script
├── references/           # Additional documentation
│   ├── REFERENCE.md     # Detailed technical reference
│   └── examples/        # Usage examples
└── assets/              # Templates and resources
    ├── templates/       # Document templates
    └── schemas/         # Data schemas
```

## Skill Development Guidelines

### Progressive Disclosure
Skills are structured for efficient context usage:
1. **Metadata** (~100 tokens): Name and description loaded at startup
2. **Instructions** (<5000 tokens): Full SKILL.md loaded when activated
3. **Resources** (as needed): Additional files loaded only when required

### Reproducible Execution
- All skill runs are logged and auditable
- Skills handle edge cases gracefully
- Clear error messages and validation
- Conservative fallback approaches

### Assumption Tracking
- Skills surface their underlying assumptions
- Changes to assumptions are versioned
- Clear separation of facts vs assumptions
- Conservative defaults when uncertain

## Current Status

This directory is a placeholder created in Step 0. Individual skills will be created in subsequent build steps:

- **Step 4**: Portfolio ingestion skill
- **Step 5**: Valuation analysis skill
- **Step 7**: monitoring rules skill
- **Step 8**: Analysis frameworks skill

## Usage

Agents automatically discover and load relevant skills based on task context. Skills are activated when:

- The task matches the skill description
- The required resources are available
- The skill's constraints are satisfied

## TODO: User Input Required

**Skill Priorities**:
- TODO: Which skill category should be developed first after Step 3?
- TODO: Are there additional skill categories needed for your investment approach?

**Skill Requirements**:
- TODO: Specific valuation frameworks to include?
- TODO: Custom monitoring rules or thresholds?
- TODO: Preferred analysis frameworks or investor lenses?

**Integration**:
- TODO: How should skills interact with each other?
- TODO: What level of skill autonomy is desired?