# Analysis Directory

Portfolio analysis layer for narrative insights and investor thinking.

## Purpose

The analysis layer turns portfolio snapshots into queryable objects, enabling thoughtful questions and answers WITHOUT re-ingesting data, running valuations, or fetching external information.

This is NOT about:
- More valuation math
- More data ingestion
- External API calls
- Automated trading signals

This IS about:
- Applying investor frameworks (Marks, Munger, Klarman)
- Surfacing what matters vs. what's noise
- Asking better questions
- Thinking, not calculating

## Directory Structure

```
analysis/
├── state/              # Portfolio state summaries
│   ├── latest.json    # Pointer to latest snapshot
│   └── summary.json   # Derived portfolio facts
├── lenses/            # Investor mental models
│   ├── marks.md       # Howard Marks: risk, cycles, what's priced in
│   ├── munger.md      # Charlie Munger: understanding, incentives, moats
│   └── klarman.md     # Seth Klarman: margin of safety, value discipline
├── answers/           # Question analysis outputs
│   └── YYYYMMDD_HHMMSS_<slug>.md
└── README.md          # This file
```

## Workflow

### Step 1: Create Summary

First, create a portfolio state summary from your latest snapshot:

```bash
./bin/investos summarize
```

This generates `analysis/state/summary.json` containing:
- Total portfolio value
- Holdings count and breakdown
- Top 5 holdings by weight
- Security type allocation (ETFs, Stocks, Other)
- Concentration flags (positions >10%)
- Recent changes (if explanation available)

**This is facts only.** No opinions, no valuations, no assumptions.

### Step 2: Ask Questions

Ask questions about your portfolio:

```bash
./bin/investos ask "Where am I most exposed?"
./bin/investos ask "What would Howard Marks worry about here?"
./bin/investos ask "What actually matters in this portfolio?"
```

The system:
1. Loads `analysis/state/summary.json`
2. Selects relevant investor lenses based on question keywords
3. Generates structured analysis with:
   - **Observations** - Facts from summary
   - **Risks** - Considerations based on lenses
   - **Open Questions** - Things to investigate
   - **What Deserves Attention** - Action items

Output is saved to `analysis/answers/` and printed to console.

## Investor Lenses

### Howard Marks Lens (`marks.md`)

**Focus:** Risk management, cycles, second-level thinking

**Key Questions:**
- Where am I exposed to permanent capital impairment?
- What's priced in versus what could happen?
- Where are we in the cycle?
- What am I assuming about rates and inflation?
- Where is concentration risk hiding?

**Use when asking about:** Risk, exposure, cycles, what could go wrong, concentration

### Charlie Munger Lens (`munger.md`)

**Focus:** Understanding, mental models, avoiding stupidity

**Key Questions:**
- Do I understand what these businesses actually do?
- What are management incentives?
- Where are the durable competitive advantages?
- What am I paying for complexity?
- Where am I making psychological mistakes?

**Use when asking about:** Understanding, incentives, moats, simplicity, mistakes

### Seth Klarman Lens (`klarman.md`)

**Focus:** Margin of safety, value discipline, capital preservation

**Key Questions:**
- What is my actual margin of safety?
- Am I investing or speculating?
- What's the catalyst for value realization?
- How liquid are my positions?
- Where am I exposed to leverage?

**Use when asking about:** Value, safety, catalysts, liquidity, downside protection

## Design Principles

### 1. Deterministic
Same inputs → same outputs. No randomness, no external dependencies.

### 2. Facts vs. Interpretation
Clear separation between:
- **Facts:** Portfolio totals, holdings, percentages (from snapshot)
- **Interpretation:** Risks, questions, attention items (from lenses)
- **Uncertainty:** Explicitly stated when data is missing

### 3. Offline-First
No external APIs, no market data fetching, no live prices. Works entirely from local files.

### 4. Conservative Tone
Raises questions rather than providing answers. Surfaces considerations rather than making recommendations.

### 5. Human-Centric
Designed for thinking and reflection, not automation. Outputs are readable narratives, not structured signals.

## Example Questions

### General Portfolio Health
- "What should I pay attention to?"
- "Where is my biggest risk?"
- "What actually matters here?"

### Risk-Focused (Marks Lens)
- "What would Howard Marks worry about?"
- "Where could I lose money permanently?"
- "What's priced into my holdings?"

### Understanding-Focused (Munger Lens)
- "Do I really understand these businesses?"
- "Where are my psychological blind spots?"
- "What would Munger think of this portfolio?"

### Value-Focused (Klarman Lens)
- "Where is my margin of safety?"
- "Am I investing or speculating?"
- "What are my catalysts?"

## Limitations

### What This System Does NOT Do

1. **No Valuation Math** - Use `investos value` for intrinsic value calculations
2. **No Market Data** - No live prices, no external feeds
3. **No Trade Recommendations** - Asks questions, doesn't give answers
4. **No Predictions** - No forecasts, no market timing
5. **No External APIs** - Completely offline

### What Could Be Missing

- **Context:** Macro environment, sector trends, news
- **Valuations:** Intrinsic value estimates (use `investos value`)
- **Fundamentals:** Business quality metrics beyond what's in snapshot
- **Performance:** Historical returns, drawdowns

The analysis layer works ONLY with what's in your portfolio snapshot and explanation files.

## Integration with Other Commands

### Before Using Analysis Layer

1. **Ingest:** `investos ingest --pdf <file>` to create snapshot
2. **Validate:** Snapshot is automatically validated during ingest
3. **(Optional) Explain:** `investos explain` to document recent changes

### Workflow Integration

```bash
# 1. Ingest new portfolio statement
./bin/investos ingest --pdf ~/Downloads/statement.pdf

# 2. Create summary
./bin/investos summarize

# 3. Ask questions
./bin/investos ask "What changed that deserves attention?"
./bin/investos ask "Where is concentration risk?"

# 4. (Optional) Review full analysis files
cat analysis/answers/20260129_*.md
```

### When to Re-Summarize

Run `investos summarize` after:
- New portfolio snapshot ingested
- Portfolio explanation generated
- Significant time has passed (weekly/monthly check-ins)

Summaries are lightweight and deterministic - safe to regenerate anytime.

## File Formats

### `analysis/state/summary.json`

```json
{
  "generated_at": "2026-01-29T10:00:00Z",
  "summary_version": "1.0.0",
  "snapshot": {
    "snapshot_id": "2026-01-29-100000",
    "timestamp": "2026-01-29T10:00:00Z"
  },
  "portfolio_totals": {
    "total_portfolio_value": 193666.76,
    "base_currency": "EUR"
  },
  "holdings_count": { "total": 14 },
  "top_holdings": [...],
  "security_type_breakdown": {...},
  "concentration": {...},
  "recent_changes": {...}
}
```

### `analysis/answers/*.md`

Markdown files with structured sections:
- Question
- Observations (Facts)
- Risks to Consider
- Open Questions
- What Deserves Attention

## Extending the System

### Adding New Lenses

To add a new investor lens:

1. Create `analysis/lenses/<name>.md` with:
   - Core philosophy
   - Key questions (6-10)
   - Application guidance

2. Update `tools/investos/ask.py`:
   - Add keywords to `_select_relevant_lenses()`
   - Add lens-specific logic to risk/question generators if needed

3. Document in this README

### Customizing Question Logic

Edit `tools/investos/ask.py`:
- `_select_relevant_lenses()` - Lens selection logic
- `_extract_observations()` - What facts to surface
- `_generate_risks()` - What risks to flag
- `_generate_questions()` - What questions to raise
- `_generate_attention_items()` - What deserves focus

Keep it conservative and deterministic.

## Philosophy

The analysis layer exists because:

1. **Numbers aren't insight** - You need mental models, not more math
2. **Questions > Answers** - Better to ask good questions than give false certainty
3. **Offline thinking** - Best analysis happens without real-time noise
4. **Investor wisdom** - Marks, Munger, Klarman have 100+ years of combined experience
5. **File-based = auditable** - Every question and answer is saved and versioned

This is a **thinking partner**, not a trading system.
