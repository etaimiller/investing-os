"""
Scaffold new artifacts (decision memos, valuations, research dossiers)

Creates structured templates aligned with Investment OS schemas and workflows.
All scaffolds include TODO markers and link to relevant schemas.
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


def scaffold_decision_memo(repo_root: Path, ticker: str, output_dir: str = "decisions") -> Path:
    """
    Create decision memo template in markdown format.
    Aligned with schema/decision-memo.schema.json structure.
    """
    decisions_dir = repo_root / output_dir
    decisions_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename: YYYY-MM-DD_TICKER_decision.md
    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    filename = f"{date_str}_{ticker}_decision.md"
    filepath = decisions_dir / filename
    
    # Generate template content
    template = f"""# Investment Decision: {ticker}

**Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
**Security**: {ticker}
**Decision Type**: TODO: [BUY / SELL / HOLD / TRIM / ADD]

**Schema Reference**: `schema/decision-memo.schema.json`

---

## Decision Summary

TODO: One-paragraph summary of the decision and primary rationale.

---

## Factual Basis

### Portfolio Context
- **Current Position**: TODO: shares owned (0 if none)
- **Position Value**: TODO: EUR
- **Portfolio Allocation**: TODO: %
- **Available Cash**: TODO: EUR
- **Snapshot Reference**: TODO: portfolio/snapshots/YYYY-MM-DD-HHMMSS.json

### Security Context
- **Current Price**: TODO: EUR
- **Price Date**: TODO: YYYY-MM-DD
- **Market Cap**: TODO: EUR
- **Recent Revenue**: TODO: EUR (source: TODO)
- **Recent Earnings**: TODO: EUR (source: TODO)

### Triggering Event
TODO: What triggered this decision review?
- Price movement?
- New research?
- Valuation update?
- Corporate action?
- Portfolio rebalancing?

---

## Assumptions

**Valuation Reference**: TODO: `valuations/models/{ticker}-valuation-YYYY-MM-DD.json`

### Key Assumptions
1. **TODO: Assumption 1**
   - Rationale: TODO
   - Sensitivity: [HIGH / MEDIUM / LOW]

2. **TODO: Assumption 2**
   - Rationale: TODO
   - Sensitivity: [HIGH / MEDIUM / LOW]

3. **TODO: Assumption 3**
   - Rationale: TODO
   - Sensitivity: [HIGH / MEDIUM / LOW]

### Assumption Risks
TODO: What could go wrong with these assumptions?

---

## Valuation Analysis

**Valuation Reference**: TODO: Link to valuation file

- **Intrinsic Value per Share**: TODO: EUR
- **Current Price**: TODO: EUR
- **Price-to-Value Ratio**: TODO: (e.g., 0.75 = trading at 75% of intrinsic value)
- **Margin of Safety (Actual)**: TODO: % (discount from intrinsic value)
- **Margin of Safety (Required)**: TODO: % (based on business quality)
- **Buy Price Target**: TODO: EUR (if buy decision)
- **Sell Price Target**: TODO: EUR (if sell decision)
- **Valuation Confidence**: [HIGH / MEDIUM / LOW]

---

## Qualitative Assessment

### Competitive Moat
- **Rating**: [WIDE / NARROW / NONE]
- **Rationale**: TODO: Why this rating? What creates the moat?
- **Durability**: TODO: How long is this advantage sustainable?

### Management Quality
- **Rating**: [EXCELLENT / GOOD / FAIR / POOR]
- **Track Record**: TODO: Evidence of value creation
- **Red Flags**: TODO: Any concerns?

### Capital Allocation
- **Rating**: [EXCELLENT / GOOD / FAIR / POOR]
- **Rationale**: TODO: Assessment of capital allocation discipline
- **Shareholder Friendliness**: TODO: Buybacks, dividends, M&A approach

### Overall Business Quality
[HIGH / MEDIUM / LOW]

---

## Risk Factors

### Identified Risks

1. **TODO: Risk 1**
   - Severity: [CATASTROPHIC / HIGH / MEDIUM / LOW]
   - Probability: [HIGH / MEDIUM / LOW]
   - Timeframe: TODO

2. **TODO: Risk 2**
   - Severity: [CATASTROPHIC / HIGH / MEDIUM / LOW]
   - Probability: [HIGH / MEDIUM / LOW]
   - Timeframe: TODO

3. **TODO: Risk 3**
   - Severity: [CATASTROPHIC / HIGH / MEDIUM / LOW]
   - Probability: [HIGH / MEDIUM / LOW]
   - Timeframe: TODO

### Risk Mitigation
TODO: How are risks mitigated through position sizing, diversification, or margin of safety?

### Risk Tolerance
TODO: Why is the risk/reward tradeoff acceptable?

---

## Decision Rationale

### Primary Reasons
1. TODO: Main reason supporting this decision
2. TODO: Second reason
3. TODO: Third reason

### Alternatives Considered

**Alternative 1**: TODO: e.g., "Hold instead of buy"
- **Why Rejected**: TODO

**Alternative 2**: TODO: e.g., "Smaller position size"
- **Why Rejected**: TODO

### Decision Criteria Met

- [ ] Sufficient margin of safety?
- [ ] Acceptable business quality?
- [ ] Manageable risk profile?
- [ ] Appropriate position size for portfolio?

### Investment Thesis
TODO: One-paragraph summary of why this investment makes sense

### Expected Holding Period
TODO: How long do you expect to hold this position?

---

## Action Plan

### Recommended Action
TODO: Specific action (e.g., "Buy 10 shares at EUR 150 or below")

### Position Sizing
- **Target Shares**: TODO
- **Target Value**: TODO: EUR
- **Target Portfolio Allocation**: TODO: %
- **Rationale**: TODO: Why this size is appropriate

### Execution Constraints
- **Price Limit**: TODO: Maximum buy / minimum sell price
- **Time Limit**: TODO: How long is this decision valid?
- **Market Conditions**: TODO: Required conditions for execution

### Review Triggers
What events should trigger decision review?
- TODO: e.g., "Price moves >20% from current level"
- TODO: e.g., "Quarterly earnings announcement"
- TODO: e.g., "Management change"

---

## Approval

**Status**: [PENDING / APPROVED / REJECTED]
**Approved By**: TODO
**Approval Date**: TODO

---

## Related Documents

- **Research**: TODO: `research/{ticker}/dossier.md`
- **Valuation**: TODO: `valuations/models/{ticker}-valuation-YYYY-MM-DD.json`
- **Portfolio Snapshot**: TODO: `portfolio/snapshots/YYYY-MM-DD-HHMMSS.json`
- **Previous Decisions**: TODO: Links to related decisions

---

## Notes

TODO: Any additional notes or context
"""
    
    with open(filepath, 'w') as f:
        f.write(template)
    
    return filepath


def scaffold_valuation_input(repo_root: Path, ticker: str, output_dir: str = "valuations/inputs") -> Path:
    """
    Create valuation input template in JSON format.
    Minimal structure for capturing key inputs before full valuation.
    """
    inputs_dir = repo_root / output_dir
    inputs_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{ticker}.json"
    filepath = inputs_dir / filename
    
    # Generate template content
    template = {
        "security_id": ticker,
        "security_name": "TODO: Full company name",
        "created_date": datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        "data_sources": [
            "TODO: List data sources (10-K, annual report, etc.)"
        ],
        "current_price": None,
        "price_date": "TODO: YYYY-MM-DD",
        "shares_outstanding": None,
        "financial_inputs": {
            "recent_revenue": None,
            "recent_revenue_year": "TODO: YYYY or TTM",
            "recent_earnings": None,
            "recent_earnings_year": "TODO: YYYY or TTM",
            "book_value": None,
            "cash_and_equivalents": None,
            "total_debt": None,
            "operating_margin": None,
            "net_margin": None
        },
        "growth_assumptions": {
            "revenue_growth_short_term": None,
            "revenue_growth_long_term": 0.03,
            "rationale": "TODO: Why these growth rates are appropriate"
        },
        "discount_rate": {
            "rate": 0.12,
            "rationale": "TODO: Why this discount rate (adjust from 12% default if needed)"
        },
        "margin_of_safety_required": 0.25,
        "notes": [
            "TODO: Add any additional notes or context",
            "This is input data only - full valuation will be in valuations/models/"
        ],
        "_schema_reference": "See schema/valuation-model.schema.json for full valuation structure"
    }
    
    import json
    with open(filepath, 'w') as f:
        json.dump(template, f, indent=2)
    
    return filepath


def scaffold_research_dossier(repo_root: Path, ticker: str, output_dir: str = "research") -> Path:
    """
    Create research dossier template in markdown format.
    Central repository for all research on a security.
    """
    dossier_dir = repo_root / output_dir / ticker
    dossier_dir.mkdir(parents=True, exist_ok=True)
    
    # Create main dossier file
    dossier_path = dossier_dir / "dossier.md"
    
    template = f"""# Research Dossier: {ticker}

**Security**: {ticker}
**Created**: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
**Last Updated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

---

## Business Overview

### What Does the Company Do?
TODO: Describe the business in simple terms
- What products/services?
- Who are the customers?
- How do they make money?

### Industry Context
TODO: Industry dynamics and positioning
- Industry size and growth
- Competitive landscape
- Regulatory environment

### Financial Summary
TODO: Key financial metrics
- Revenue: TODO
- Earnings: TODO
- Margins: TODO
- Returns on capital: TODO

---

## Competitive Moat Assessment

### Moat Rating
[WIDE / NARROW / NONE]

### Moat Sources
TODO: What creates sustainable competitive advantages?
- [ ] Network effects
- [ ] Switching costs
- [ ] Brand/reputation
- [ ] Cost advantages
- [ ] Regulatory protection
- [ ] Patents/IP

### Moat Durability
TODO: How long will these advantages last?

### Threats to Moat
TODO: What could erode competitive advantages?

---

## Management Quality

### Key Executives
TODO: List key management team members
- CEO: TODO
- CFO: TODO
- Other key roles: TODO

### Track Record
TODO: Evidence of value creation
- Historical performance
- Capital allocation decisions
- Strategic initiatives

### Compensation
TODO: How is management compensated?
- Alignment with shareholders?
- Any red flags?

### Communication
TODO: Quality of investor communications
- Transparent?
- Consistent?
- Realistic?

---

## Capital Allocation

### Historical Approach
TODO: How has management allocated capital?
- Organic growth
- Acquisitions
- Dividends
- Share buybacks
- Debt paydown

### Quality Assessment
[EXCELLENT / GOOD / FAIR / POOR]

TODO: Evidence of discipline and shareholder focus

---

## Risk Factors

### Business Risks
1. TODO: Key business risk 1
2. TODO: Key business risk 2
3. TODO: Key business risk 3

### Financial Risks
1. TODO: Debt levels, margin compression, etc.

### Market/Industry Risks
1. TODO: Cyclicality, disruption, competition

### Management/Governance Risks
1. TODO: Succession, conflicts of interest, etc.

---

## Investment Thesis

### Bull Case
TODO: What has to go right for this to be a great investment?
1. TODO
2. TODO
3. TODO

### Bear Case
TODO: What could go wrong?
1. TODO
2. TODO
3. TODO

### Base Case
TODO: Most likely scenario

---

## Catalysts

### Positive Catalysts
TODO: What could drive the stock higher?
- New products/services
- Market expansion
- Operational improvements
- Industry tailwinds

### Negative Catalysts
TODO: What could drive the stock lower?
- Competition
- Regulatory changes
- Market conditions
- Company-specific issues

---

## Valuation

### Historical Valuation
TODO: How has the market valued this company historically?
- P/E range
- P/B range
- EV/EBITDA range
- Other relevant multiples

### Current Valuation
TODO: Current valuation metrics
- Current P/E: TODO
- Current P/B: TODO
- Relative to history: [CHEAP / FAIR / EXPENSIVE]

### Intrinsic Value Estimate
See: `valuations/models/{ticker}-valuation-YYYY-MM-DD.json`

TODO: Summary of intrinsic value estimate and margin of safety

---

## Key Questions / Uncertainties

1. TODO: What are the key unknowns?
2. TODO: What additional research is needed?
3. TODO: What would change your thesis?

---

## Research Sources

### Primary Sources
- [ ] Annual reports (10-K)
- [ ] Quarterly reports (10-Q)
- [ ] Earnings calls
- [ ] Investor presentations
- [ ] Company website

### Secondary Sources
- [ ] Analyst reports (which firms?)
- [ ] Industry research
- [ ] News articles
- [ ] Other: TODO

### Key Documents
TODO: List specific important documents with dates/links

---

## Research Log

### {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
- Created initial research dossier
- TODO: Document research activities and findings

### Future Updates
- TODO: Date updates as research progresses
- TODO: Note material changes to thesis or understanding

---

## Related Files

- **Valuation**: `valuations/models/{ticker}-valuation-YYYY-MM-DD.json`
- **Decisions**: `decisions/*_{ticker}_decision.md`
- **Portfolio Snapshots**: `portfolio/snapshots/*.json` (for current holdings)
"""
    
    with open(dossier_path, 'w') as f:
        f.write(template)
    
    # Create README for the ticker directory
    readme_path = dossier_dir / "README.md"
    readme_content = f"""# {ticker} Research Directory

This directory contains all research materials for {ticker}.

## Contents

- `dossier.md` - Main research dossier (comprehensive overview)
- Additional files:
  - Financial models
  - Notes from earnings calls
  - Competitor analysis
  - Industry research
  - etc.

## Organization

Keep all research for {ticker} in this directory for easy reference.
Link to dossier.md from decision memos and valuations.
"""
    
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    return dossier_path
