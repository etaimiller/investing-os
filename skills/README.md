# Investment OS Agent Skills Pack

Agent Skills for the Investment OS repository, following the [Agent Skills Specification](https://agentskills.io/specification).

## Overview

This skills pack provides AI agents with structured, executable knowledge for operating the Investment OS. Each skill defines **when to use it**, **how to execute it**, **how to verify success**, and **how to handle failures**.

**Design Principles:**
- Deterministic and offline-first
- Conservative assumptions
- Human-in-the-loop always
- No trade execution
- No external data fetching
- Clear separation of facts from judgment

## Skills Directory Structure

```
skills/
├── repo-cheatsheet/      Command index and workflow map
├── portfolio-ingest/     Ingest Trade Republic PDFs → snapshots
├── portfolio-health/     System health checks and diagnostics
├── portfolio-explain/    Mechanical change attribution
├── portfolio-valuation/  Offline, deterministic valuations
├── portfolio-qa/         Question answering with investor lenses
├── decision-memos/       Structured decision frameworks
└── README.md            This file
```

## Skill Summaries

### 1. repo-cheatsheet
**Purpose:** Command index and workflow routing  
**Use when:** User asks "what can I do?" or agent needs capability overview  
**Key output:** Command recommendations and workflow sequences  

Provides agents with complete knowledge of available operations, Makefile targets, and typical workflow patterns. Acts as a "front door" for dispatching to more specific skills.

### 2. portfolio-ingest
**Purpose:** Import Trade Republic PDF statements into canonical JSON snapshots  
**Use when:** User provides PDF or asks to load/import portfolio data  
**Key output:** Timestamped snapshot in portfolio/snapshots/  

Entry point for all portfolio data. Creates immutable, schema-validated snapshots that serve as source of truth for downstream analysis.

### 3. portfolio-health
**Purpose:** Verify repository integrity and validate system state  
**Use when:** Starting session, debugging issues, or before complex operations  
**Key output:** Health status report with errors/warnings  

Read-only diagnostic tool that checks directory structure, schemas, snapshots, and configuration. Reports problems without attempting fixes.

### 4. portfolio-explain
**Purpose:** Attribute portfolio changes between two snapshots  
**Use when:** User asks "what changed?" or wants to understand value movements  
**Key output:** Mechanical attribution report (price/quantity/new/removed changes)  

Deterministic change decomposition. Answers "what changed" not "why it changed" - pure mechanical attribution without external context.

### 5. portfolio-valuation
**Purpose:** Calculate offline, assumption-driven intrinsic values  
**Use when:** User asks to "value" holdings or wants intrinsic value estimates  
**Key output:** Per-holding valuation files with margin of safety calculations  

Conservative DCF-based valuations for stocks. ETFs treated as allocation vehicles. Requires user-provided fundamental data. Reproducible and deterministic.

### 6. portfolio-qa
**Purpose:** Answer portfolio questions using investor lenses  
**Use when:** User asks open-ended questions about portfolio  
**Key output:** Structured analysis with observations, risks, questions  

Applies Marks/Munger/Klarman frameworks to portfolio state. Creates narrative insights without recommendations. Two-step process: summarize then ask.

### 7. decision-memos
**Purpose:** Generate structured decision frameworks for portfolio actions  
**Use when:** User considers buy/sell/hold decisions  
**Key output:** Decision memo template with lens-based analysis prompts  

Creates thinking frameworks for capital allocation decisions. Structures judgment without making recommendations. Always requires human completion and execution.

## Workflow Composition

Skills compose into complete workflows:

### New Portfolio Data Workflow
```
portfolio-ingest → portfolio-health → portfolio-explain → portfolio-qa
```

1. **Ingest** new PDF statement
2. **Health check** to verify success
3. **Explain** changes from previous snapshot
4. **Ask** "What changed that deserves attention?"

### Portfolio Review Workflow
```
portfolio-health → portfolio-qa → decision-memos
```

1. **Health check** to ensure system ready
2. **Summarize and ask** questions about current state
3. **Create decision memo** for specific actions being considered

### Valuation Workflow
```
portfolio-health → portfolio-valuation → portfolio-qa
```

1. **Health check** repository
2. **Run valuation** on holdings
3. **Ask** "What looks undervalued?" (interprets valuation results)

### Complete Decision Workflow
```
portfolio-ingest → portfolio-explain → portfolio-qa → decision-memos
```

1. **Ingest** latest statement
2. **Explain** what changed mechanically
3. **Ask** risk/concentration questions
4. **Create decision memo** for specific action
5. User fills memo and decides
6. User executes manually (if proceeding)

## Skill Usage Patterns

### Starting New Session
Always begin with health check:
```
repo-cheatsheet → portfolio-health → [specific skill]
```

### User Has Question
Route through cheatsheet first:
```
repo-cheatsheet → portfolio-qa OR portfolio-explain OR decision-memos
```

### User Wants Action
Always go through decision memo:
```
portfolio-qa → decision-memos → [human execution]
```

### User Provides PDF
Standard ingestion flow:
```
portfolio-ingest → portfolio-explain → portfolio-qa
```

## Conservative Design

All skills follow these principles:

**Deterministic:**
- Same inputs → same outputs (excluding timestamps)
- No random variation
- Reproducible for audit trail

**Offline-First:**
- No external APIs
- No market data fetching
- No real-time prices
- All data from local files

**Human-in-the-Loop:**
- System structures thinking
- Human makes decisions
- Human executes actions
- No auto-execution ever

**Facts vs. Judgment:**
- Clear separation maintained
- Facts from portfolio state
- Judgment requires human input
- Missing data stated, not invented

**Conservative Assumptions:**
- When uncertain, ask user
- Warnings acceptable, errors stop
- Incomplete better than invented
- "Do nothing" is valid outcome

## Skill Composition Rules

**Prerequisites:**
- Always check health before complex operations
- Always summarize before asking questions
- Always have snapshot before making decisions

**Sequencing:**
- Ingest → Health → Explain → Summarize → Ask → Decide
- Each step validates before proceeding
- Failures stop workflow, don't skip

**Parallel:**
- Health check can run anytime
- Multiple questions can be asked in sequence
- Multiple decision memos can be created

**Never:**
- Skip validation steps
- Proceed with broken state
- Invent missing data
- Execute trades automatically

## Error Handling Philosophy

**Critical Errors (Stop):**
- Missing directories
- Invalid schemas
- Broken snapshots (latest)
- No portfolio data

**Warnings (Continue):**
- Old snapshots invalid
- Missing fundamentals
- Incomplete valuations
- High residuals in explanation

**User Clarification (Ask):**
- Unclear intent
- Missing parameters
- Multiple valid interpretations
- Stale data

## Agent Reasoning Guidelines

**When User Request is Unclear:**
1. Consult repo-cheatsheet for capabilities
2. Ask clarifying questions
3. Suggest 2-3 most likely workflows
4. Don't guess user intent

**When Prerequisites Missing:**
1. Identify what's missing
2. Suggest prerequisite command
3. Explain why it's needed
4. Wait for user confirmation

**When Errors Occur:**
1. Report exact error message
2. Classify severity (critical/warning)
3. Suggest recovery action
4. Don't attempt automatic fixes

**When Data is Stale:**
1. Check dates/timestamps
2. Inform user of staleness
3. Suggest refresh command
4. Proceed only with user OK

**When Multiple Options Exist:**
1. Present alternatives clearly
2. Explain differences
3. Recommend if obvious
4. Let user choose

## Integration with Investment OS

Skills are tightly coupled to Investment OS commands:

**Makefile Targets:**
- `make doctor` → portfolio-health
- `make ingest` → portfolio-ingest
- `make summarize` → portfolio-qa
- `make ask` → portfolio-qa
- `make explain` → portfolio-explain
- `make value` → portfolio-valuation
- `make decide` → decision-memos

**CLI Commands:**
All Makefile targets have equivalent `./bin/investos` commands documented in each skill.

**Preferred Usage:**
- Use Makefile targets (shorter, documented)
- Fall back to CLI for advanced options
- Document both in skills

## Repository Context

**Data Flow:**
```
Raw PDF → Snapshot → Summary → Analysis → Decision
```

**File Locations:**
- `portfolio/raw/` - Original PDFs
- `portfolio/snapshots/` - Canonical JSON snapshots
- `analysis/state/` - Portfolio summaries
- `analysis/answers/` - Question analyses
- `decisions/` - Decision memos
- `valuations/outputs/` - Valuation results
- `monitoring/explanations/` - Change attributions

**Immutability:**
- Snapshots never modified
- Analysis outputs timestamped
- Git history provides audit trail
- All changes traceable

## Compliance

This skills pack complies with:

1. **Agent Skills Specification** (https://agentskills.io/specification)
   - Mandatory frontmatter structure
   - Required sections (When/Preconditions/Steps/Verification/Failures)
   - Deterministic execution
   - Clear failure modes

2. **Claude Agent Skills Conventions** (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
   - Explicit tool allowlisting
   - Conservative assumptions
   - Human-in-the-loop design
   - No recommendations or execution

## Support

**For Agents:**
- Start with repo-cheatsheet for capability overview
- Use portfolio-health for diagnostics
- Follow workflow patterns above
- Ask user for clarification when uncertain

**For Humans:**
- Skills are for AI agents, not human reading
- See CHEATSHEET.md for human-friendly commands
- See README.md for project overview
- See individual tool READMEs for details

## Version

Skills pack version: 1.0.0  
Investment OS version: 1.0.0  
Last updated: 2026-01-29
