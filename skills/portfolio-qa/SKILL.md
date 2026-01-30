---
name: portfolio-qa
description: |
  Answer portfolio questions using investor lenses (Howard Marks, Charlie Munger,
  Seth Klarman). This skill creates portfolio summaries and applies structured
  thinking frameworks to generate narrative insights. All analysis is based on
  portfolio state only - no external data, predictions, or recommendations.
allowed_tools:
  - Makefile:summarize
  - Makefile:ask
  - Bash:./bin/investos summarize
  - Bash:./bin/investos ask "<question>"
  - Bash:ls analysis/state/
  - Bash:cat analysis/state/summary.json
inputs:
  - question: User's portfolio question (natural language)
outputs:
  - summary_json: Deterministic portfolio facts (if summarize run)
  - analysis_markdown: Structured analysis with observations, risks, questions
  - lens_selection: Which investor frameworks applied
artifacts:
  - analysis/state/summary.json: Portfolio facts (total value, holdings, concentration)
  - analysis/state/latest.json: Pointer to latest snapshot
  - analysis/answers/<timestamp>_<slug>.md: Full question analysis
  - logs/runs/YYYY-MM-DD/HHMMSS_summarize.json: Summarize log
  - logs/runs/YYYY-MM-DD/HHMMSS_ask.json: Ask log
failure_modes:
  - no_snapshot: No portfolio snapshot exists to summarize
  - no_summary: Summary.json doesn't exist (need to run summarize first)
  - question_too_vague: Can't select appropriate lenses
examples:
  - "What should I pay attention to?"
  - "Where is my biggest risk?"
  - "What would Howard Marks worry about?"
  - "Do I understand these businesses?"
---

# SKILL: portfolio-qa

## WHEN TO USE THIS SKILL

Use this skill when:
- User asks open-ended questions about their portfolio
- User wants narrative insights, not just numbers
- User asks about risk, concentration, understanding
- User mentions investor names (Marks, Munger, Klarman)
- User asks "what should I do?" or "what matters?"

Do NOT use this skill when:
- User wants specific data (holdings list, total value) - use snapshot directly
- User wants valuations - use portfolio-valuation
- User wants change attribution - use portfolio-explain
- User wants trade execution - not supported

## PRECONDITIONS

**Required:**
- At least one portfolio snapshot exists
- Repository structure intact (run `make doctor` if uncertain)

**Workflow:**
1. First run `summarize` to create queryable state
2. Then run `ask` with questions

**Summary Must Be Recent:**
- If portfolio changed (new ingestion), re-run summarize
- Summary is cached, not auto-updated

## STEP-BY-STEP PROCEDURE

### Step 1: Create or Update Portfolio Summary

**Check if summary exists:**
```bash
ls -lh analysis/state/summary.json
```

**If missing or old, create it:**
```bash
make summarize
```

**Expected output:**
```
Creating portfolio summary...

✓ Summary created!

Snapshot: 2026-01-29-143022
Date: 2026-01-29T14:30:22Z

Portfolio Value: 193,666.76 EUR
Cash: 0.00 EUR

Holdings: 14 total, 14 valued

Security Types:
  ETF     :  5 holdings,  50.2%
  Stock   :  9 holdings,  49.8%

Top 5 Holdings:
   20.5% - iShsIV-EO Ultrashort Bd U.ETF
   10.7% - iShs IV-iShs MSCI India UC.ETF
   10.1% - Fairfax Finl Holdings Ltd.
   10.1% - Berkshire Hathaway Inc.
    9.7% - InvescoMI S&P 500 ETF

⚠ Concentration Flags: 4 holdings over 10%

Output: analysis/state/summary.json
```

### Step 2: Verify Summary Created

```bash
cat analysis/state/summary.json | head -20
```

**Expected fields:**
- generated_at
- snapshot.snapshot_id
- portfolio_totals
- holdings_count
- top_holdings
- security_type_breakdown
- concentration

### Step 3: Ask Portfolio Question

**Using Makefile (PREFERRED):**
```bash
make ask Q="What should I pay attention to?"
```

**Using CLI directly:**
```bash
./bin/investos ask "What should I pay attention to?"
```

**Example questions:**

**General:**
```bash
./bin/investos ask "What should I pay attention to?"
./bin/investos ask "Where is my biggest risk?"
./bin/investos ask "What actually matters in this portfolio?"
```

**Risk-focused (Marks lens):**
```bash
./bin/investos ask "What would Howard Marks worry about?"
./bin/investos ask "Where could I lose money permanently?"
./bin/investos ask "Where is concentration risk hiding?"
```

**Understanding-focused (Munger lens):**
```bash
./bin/investos ask "Do I understand these businesses?"
./bin/investos ask "Where are my psychological blind spots?"
./bin/investos ask "What would Munger think of this portfolio?"
```

**Value-focused (Klarman lens):**
```bash
./bin/investos ask "Where is my margin of safety?"
./bin/investos ask "Am I investing or speculating?"
./bin/investos ask "Which positions have clear catalysts?"
```

### Step 4: Read Console Output

**Expected output structure:**
```
Analyzing: What should I pay attention to?

## Observations (Facts)
- Portfolio value: 193,667 EUR
- Holdings: 14 positions
- Allocation: 50% ETF, 50% Stock
  ... and 3 more

## Risks to Consider
- Concentration risk: 20% in iShsIV-EO Ultrashort Bd U.ETF
  creates single-position downside exposure

## Open Questions
- Where are we in the cycle? Are these holdings positioned
  defensively or aggressively?
  ... and 3 more

## What Deserves Attention
- Review largest position (20%) - Ensure thesis still valid
- High concentration: 4 positions over 10%
- Review recent portfolio changes

✓ Full analysis saved to: analysis/answers/20260129_143530_what_should_i_pay_attention_to.md
```

### Step 5: Review Full Analysis (Optional)

```bash
cat analysis/answers/<timestamp>_<slug>.md
```

**Full markdown includes:**
- Question
- Lenses applied
- Detailed observations
- Risk considerations
- Open questions
- Action items
- Disclaimers

## VERIFICATION & SUCCESS CRITERIA

**Summarize succeeded if:**
1. Command exits with status 0
2. "✓ Summary created!" appears
3. analysis/state/summary.json exists
4. Holdings count > 0 (unless portfolio empty)

**Ask succeeded if:**
1. Command exits with status 0
2. Structured output printed to console
3. Markdown file created in analysis/answers/
4. Appropriate lenses selected

## FAILURE HANDLING & RECOVERY

### No Snapshot to Summarize
**Symptom:** "✗ No portfolio snapshots found"

**Recovery:**
1. User needs to ingest data first
2. Suggest: `make ingest PDF=<path>`
3. Do not proceed with summarize

**Do NOT:**
- Create empty summary
- Use old data
- Invent portfolio state

### No Summary for Ask
**Symptom:** "✗ No portfolio summary found. Run 'investos summarize' first."

**Recovery:**
1. Run summarize first:
   ```bash
   make summarize
   ```
2. Then retry ask

**Do NOT:**
- Skip summarize step
- Use stale summary without checking
- Proceed without portfolio state

### Question Too Vague
**Symptom:** Generic answer that doesn't address user intent

**Recovery:**
1. Ask user to be more specific
2. Suggest example questions:
   - "Where is my biggest risk?"
   - "What would Marks worry about?"
   - "Do I understand these holdings?"
3. Offer multiple lens perspectives

**Do NOT:**
- Make assumptions about user intent
- Provide generic advice
- Invent concerns not grounded in portfolio

### Stale Summary
**Symptom:** Summary date doesn't match latest snapshot

**Recovery:**
1. Check summary date: `cat analysis/state/summary.json | grep generated_at`
2. Check latest snapshot: `ls -lt portfolio/snapshots/*.json | head -1`
3. If mismatch, re-run summarize
4. Inform user: "Summary is old. Updating now."

**Do NOT:**
- Use stale summary without informing user
- Assume summary is current
- Skip update

## UNDERSTANDING LENS SELECTION

System automatically selects lenses based on question keywords:

**Marks lens triggers:**
- risk, cycle, exposed, impair, permanent loss
- what could go wrong, downside, priced in
- concentration, correlated

**Munger lens triggers:**
- understand, know, competence, incentive
- moat, advantage, competitive, simple, complex
- mistake, bias, psychology

**Klarman lens triggers:**
- margin, safety, value, cheap, expensive
- catalyst, liquid, asset, tangible, downside protection
- speculation, worth

**Default:** All three lenses if no clear trigger

## ANSWER STRUCTURE

Every answer includes four sections:

### 1. Observations (Facts)
**What it contains:**
- Portfolio totals and holdings count
- Security type breakdown
- Top holdings by weight
- Concentration flags
- Recent changes (if available)

**Example:**
```
- Portfolio value: 193,667 EUR
- Holdings: 14 positions
- Allocation: 50% ETF, 50% Stock
- Concentration: 4 holdings over 10%
```

### 2. Risks to Consider
**What it contains:**
- Concentration risks (>10% positions)
- Type imbalances (too much in one category)
- Classification uncertainty
- Data quality issues

**Example:**
```
- Concentration risk: 20% in single position creates
  single-point downside exposure
- Individual stock concentration: 50% requires deep
  understanding of each business
```

### 3. Open Questions
**What it contains:**
- Lens-specific prompts
- Things to investigate
- Gaps in understanding
- Assumption checks

**Example:**
```
- Where are we in the cycle?
- Do I truly understand how <holding> makes money?
- What is my actual margin of safety?
```

### 4. What Deserves Attention
**What it contains:**
- Specific holdings to review
- Concentration to address
- Recent changes to investigate
- Classifications to verify

**Example:**
```
- Review largest position (20%) - ensure thesis valid
- High concentration: 4 positions over 10%
- Recent portfolio changes need investigation
```

## NOTES FOR AGENT REASONING

**Design Intent:**
Portfolio QA is a **thinking partner**, not an answer provider. It surfaces questions and considerations based on portfolio facts and investor frameworks.

**No Recommendations:**
System NEVER says:
- "Buy this"
- "Sell that"
- "Reduce exposure"
- "You should..."

Instead, it asks:
- "Where could this go wrong?"
- "Do you understand this?"
- "What protects you here?"

**Facts vs. Interpretation:**

**Facts (from summary):**
- Portfolio value
- Holdings count
- Weights and percentages
- Concentration flags
- Recent changes

**Interpretation (from lenses):**
- Risk considerations
- Understanding questions
- Safety margin queries
- Action items for review

**Clear separation maintained throughout.**

**Deterministic Output:**
Given same summary, same question produces same answer structure (excluding timestamps). This ensures:
- Reproducibility
- Audit trail
- No random variation

**Offline-First:**
System uses ONLY:
- Portfolio snapshots (Step 4)
- Portfolio summaries (analysis/state/summary.json)
- Explanation files (Step 6, if available)
- Static lens files (analysis/lenses/*.md)

Does NOT use:
- Live prices
- Market data
- News or commentary
- External APIs
- Forecasts or predictions

**Conservative Tone:**
- Raises questions, doesn't answer them
- Explicit about uncertainty
- "Do nothing" is valid outcome
- Missing data stated, not inferred

**Composition with Other Skills:**

Typical workflow:
```
1. make ingest PDF=<file>           (if new data)
2. make summarize                   (create queryable state)
3. make ask Q="<question>"          (get insights)
4. make decide --isin <ISIN>        (if action considered)
```

**When to Re-Summarize:**
- After new ingestion
- After portfolio changes
- Weekly/monthly check-ins
- Before important questions

**Interpreting Answers:**

**Many concentration flags:**
- Normal for focused portfolios
- Not inherently bad
- Prompts for understanding check

**High ETF percentage:**
- Lower individual security risk
- Less control over holdings
- Different from stock concentration

**"Other" category large:**
- May include complex securities
- Needs classification review
- Not necessarily problematic

**Conservative Approach:**
- Don't invent concerns
- Don't exaggerate risks
- Don't assume user intent
- Always base on portfolio facts
- Explicit about what's unknown
