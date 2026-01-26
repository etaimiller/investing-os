# Decisions Directory

This directory contains all investment decision records and supporting analysis.

## What Belongs Here

- **Decision memos** - Complete rationale for buy/sell/hold decisions
- **Trade plans** - Specific trade execution plans (for human execution only)
- **Decision frameworks** - Templates and checklists for decision-making
- **Decision history** - Complete audit trail of all investment decisions

## File Naming Convention

- **Decision memos**: `[TICKER]-decision-YYYY-MM-DD-HHMMSS.md`
- **Trade plans**: `[TICKER]-trade-plan-YYYY-MM-DD.md`
- **Framework updates**: `framework-update-YYYY-MM-DD.md`

## Decision Framework

Every investment decision must include:

1. **Factual Basis** - Current portfolio state and security information
2. **Assumptions** - Clear statement of all assumptions made
3. **Valuation Analysis** - Conservative intrinsic value with margin of safety
4. **Qualitative Assessment** - Moat, management, capital allocation discipline
5. **Risk Factors** - Specific risks and mitigating factors
6. **Decision Rationale** - Complete explanation of why this action is recommended

## Workflow Integration

1. **Research Phase** - Research directory provides security analysis
2. **Valuation Phase** - Valuations directory provides intrinsic value analysis
3. **Decision Phase** - Create comprehensive decision memo
4. **Human Review** - Human reviews and approves decision
5. **Execution Planning** - Create trade plan for human execution
6. **Post-Decision** - Record outcomes and lessons learned

## When to Look Here

- **Decision making** - Review complete decision rationale before acting
- **Portfolio review** - Understand past decisions and their outcomes
- **Audit trail** - Complete record of investment decisions
- **Process improvement** - Learn from decision accuracy over time

## Directory Structure

```
decisions/
├── memos/             # Complete decision memos with full rationale
├── trade-plans/       # Trade execution plans (human execution only)
├── frameworks/        # Decision templates and checklists
└── history/          # Decision outcomes and performance tracking
```

## Decision Memo Template

### Investment Decision: [TICKER] - [BUY/SELL/HOLD]
**Date:** YYYY-MM-DD
**Security:** [Company Name - Ticker]

### Factual Basis
- Current portfolio allocation
- Security current price and market position
- Company financial position

### Assumptions
- Growth rate assumptions
- Market condition assumptions
- Economic environment assumptions

### Valuation Analysis
- Intrinsic value calculation
- Margin of safety assessment
- Comparison to current price

### Qualitative Assessment
- Competitive moat strength
- Management quality assessment
- Capital allocation discipline

### Risk Factors
- Specific business risks
- Market risks
- Mitigating factors

### Decision Rationale
- Complete explanation of decision
- Alternative scenarios considered
- Why this action is recommended

## TODO: User Input Required

**Decision Criteria:**
- TODO: What minimum criteria must be met for buy decisions?
- TODO: What triggers sell decisions?
- TODO: When are hold decisions appropriate?

**Approval Process:**
- TODO: What information must be included in decision memos?
- TODO: How should risk be quantified and presented?

**Performance Tracking:**
- TODO: How should decision accuracy be measured?
- TODO: What metrics track decision quality over time?

## Notes

- **NO TRADE EXECUTION** - System never executes trades, only provides analysis
- All decisions require explicit human approval
- Decision memos create complete audit trail
- Track decision outcomes to improve process over time
- Conservative bias when uncertainty exists