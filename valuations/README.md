# Valuations Directory

This directory contains all security valuation analyses and intrinsic value calculations.

## What Belongs Here

- **Valuation models** - Intrinsic value calculations using various methodologies
- **Assumptions** - Underlying assumptions for each valuation model
- **Margin of safety** - Analysis of price vs intrinsic value
- **Valuation history** - Historical valuations for tracking accuracy

## File Naming Convention

- **Valuation models**: `[TICKER]-valuation-YYYY-MM-DD.json`
- **Assumptions**: `[TICKER]-assumptions-YYYY-MM-DD.json`
- **Analysis summary**: `[TICKER]-summary-YYYY-MM-DD.md`

## Valuation Methodologies

1. **Intrinsic Value** - DCF-based fundamental valuation
2. **Relative Valuation** - Comparison to peers and market multiples
3. **Asset-Based** - Net asset value and liquidation value
4. **Qualitative Adjustments** - Moat, management, capital allocation quality

## Workflow Integration

1. **Research Input** - Use research directory findings for valuation inputs
2. **Model Creation** - Build conservative valuation models
3. **Assumption Documentation** - Clearly state all assumptions
4. **Margin Analysis** - Calculate required margin of safety
5. **Decision Support** - Support buy/sell/hold decisions

## When to Look Here

- **Before buying** - Determine if security offers sufficient margin of safety
- **Portfolio review** - Re-evaluate existing holdings
- **Market movements** - Update valuations when fundamentals change
- **Decision making** - Support investment recommendations

## Directory Structure

```
valuations/
├── models/            # Valuation calculations and models (JSON)
├── assumptions/       # Underlying assumptions by security
│   └── conservative.yaml  # Conservative assumption template
├── history/          # Historical valuations for accuracy tracking
└── summaries/        # Valuation summaries and conclusions
```

## Data Format

Valuations follow the **valuation-model.schema.json** schema located in `schema/`.

**Key format principles**:
- Separates assumptions, facts, and calculated intrinsic value
- All assumptions must be explicitly stated with rationale
- Links to assumption templates (e.g., conservative.yaml)
- Includes qualitative assessment alongside quantitative analysis

**Assumption Template**: See `valuations/assumptions/conservative.yaml` for default conservative assumptions

## Valuation Principles

- **Conservative by default** - When uncertain, choose more conservative approach
- **Assumption-driven** - Every valuation must surface its assumptions
- **Margin of safety** - Require discount to intrinsic value
- **Qualitative integration** - Combine quantitative with qualitative factors

## Valuation Components

**Quantitative Analysis:**
- Discounted cash flow models
- Earnings multiples and growth rates
- Balance sheet and cash flow analysis
- Historical performance trends

**Qualitative Assessment:**
- Competitive moat and market position
- Management quality and track record
- Capital allocation discipline
- Industry and competitive dynamics

## TODO: User Input Required

**Valuation Methods:**
- TODO: Which valuation methodologies should be prioritized?
- TODO: What minimum margin of safety is required?

**Assumption Rules:**
- TODO: How should growth rates be determined?
- TODO: What discount rates should be used for different security types?

**Update Frequency:**
- TODO: How often should valuations be reviewed?
- TODO: What triggers valuation updates?

## Notes

- Valuations are estimates, not precise calculations
- Always document assumptions and reasoning
- Track valuation accuracy over time
- Valuations should support, not drive, investment decisions
- Conservative approach when assumptions are uncertain