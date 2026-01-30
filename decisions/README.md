# Decisions Directory

Investment decision records created through structured thinking, not automation.

## Purpose

This directory stores **decision-grade memos** that:
- Frame portfolio actions with explicit reasoning
- Apply investor lenses (Marks, Munger, Klarman)
- Separate facts from judgment
- Make "do nothing" an explicit choice
- Create durable audit trail

**This is NOT about**:
- Trade signals or recommendations
- Automated decision-making
- Market predictions
- External data or news

**This IS about**:
- Structured judgment
- Explicit reasoning
- Thinking tool, not action tool
- Human-in-the-loop always

## Creating Decision Memos

### Command

```bash
./bin/investos decide --isin <ISIN> --action <action>
```

### Actions

- **`new`** - Consider initiating new position
- **`add`** - Consider adding to existing position
- **`trim`** - Consider reducing position size
- **`exit`** - Consider closing position
- **`hold`** - Review and maintain current position (default)

### Examples

```bash
# Review existing holding
./bin/investos decide --isin US0378331005

# Consider adding to position
./bin/investos decide --isin US0378331005 --action add

# Consider new position
./bin/investos decide --action new --name "Apple Inc." --isin US0378331005

# Add context notes
./bin/investos decide --isin IE00B4L5Y983 --action trim \
  --notes "Position grew to 20% via appreciation"

# Use specific lens
./bin/investos decide --isin US0846707026 --lens klarman

# Just create template
./bin/investos decide --isin US5949181045 --emit-template-only
```

## Decision Memo Structure

Every memo follows this structure:

### 1. Decision Framing (Facts Only)
- What decision is being considered?
- What changed (or didn't)?
- What is known vs unknown?

### 2. Portfolio Context
- Current weight and concentration impact
- Recent portfolio changes (from Step 6 explanations)
- Correlation notes

### 3. Investor Lens Review

**Howard Marks — Risk & Cycles:**
- Where could permanent capital loss occur?
- What assumptions must be true?
- What is priced in?

**Charlie Munger — Understanding & Incentives:**
- Do I understand the business?
- Where could I be fooling myself?
- Incentives and complexity flags

**Seth Klarman — Margin of Safety:**
- What protects me if I'm wrong?
- What is the downside case?
- Liquidity and optionality

### 4. Disconfirming Evidence
- What would make this decision wrong?
- What evidence would change my mind?

### 5. Alternatives Considered
- Do nothing (explicit evaluation)
- Reduce exposure elsewhere
- Delay decision

### 6. Decision Status
- ☐ Proceed
- ☐ Delay
- ☐ Reject

### 7. Follow-ups & Triggers
- What should I monitor?
- What would force a revisit?

## File Naming Convention

```
YYYY-MM-DD_<isin-or-slug>_<action>.md
```

Examples:
- `2026-01-29_US0378331005_add.md`
- `2026-01-29_IE00B4L5Y983_trim.md`
- `2026-01-29_new_position_hold.md`

## Data Sources

Decision memos use ONLY:
- Portfolio snapshots (Step 4)
- Portfolio summaries (Step 7)
- Explanation outputs (Step 6)
- Static investor lens files

**No external data:**
- No live prices
- No market data
- No news or commentary
- No API calls

Missing data is stated explicitly, never inferred.

## Workflow

### Complete Decision Workflow

1. **Ensure portfolio is current:**
   ```bash
   # If needed, ingest new statement
   ./bin/investos ingest --pdf ~/Downloads/statement.pdf
   
   # Create summary
   ./bin/investos summarize
   ```

2. **Create decision memo:**
   ```bash
   ./bin/investos decide --isin <ISIN> --action <action>
   ```

3. **Fill in analysis:**
   - Edit the generated markdown file
   - Complete all [TODO] sections
   - Add your reasoning to each lens section
   - List disconfirming evidence
   - Evaluate alternatives

4. **Make decision:**
   - Check one box: Proceed / Delay / Reject
   - Write clear rationale

5. **If proceeding:**
   - Execute manually (system NEVER auto-executes)
   - Record outcome for future review

## Design Principles

### Deterministic
Same portfolio state → same memo structure (excluding timestamps)

### Facts vs. Judgment
- **Facts:** Portfolio weights, recent changes, concentration
- **Judgment:** Risk assessment, understanding evaluation, safety margins
- Clear separation throughout memo

### Conservative Tone
- Raises questions, doesn't provide answers
- Explicit about uncertainty
- "Do nothing" is a valid outcome

### No Recommendations
System structures thinking but never says "buy" or "sell"

### Everything Written
All reasoning captured in durable files, versioned in git

## Integration with Other Steps

### Prerequisites
- **Step 4:** Portfolio snapshot must exist
- **Step 7:** `investos summarize` recommended (provides context)

### Optional but Helpful
- **Step 6:** Explanation of recent changes
- **Step 5:** Valuation analysis (run separately)

### After Decision
- Manual trade execution (if proceeding)
- Update portfolio via new PDF ingest
- Run explanation to understand change

## Examples

### Example 1: Reviewing Concentrated Position

```bash
$ ./bin/investos decide --isin IE00BCRY6557 --action hold

Creating decision memo...

Action: hold
ISIN: IE00BCRY6557
Lenses: marks, munger, klarman
Snapshot: 2026-01-26-224637.json

✓ Decision memo created!

Output: decisions/2026-01-29_IE00BCRY6557_hold.md

Next steps:
  1. Edit decisions/2026-01-29_IE00BCRY6557_hold.md
  2. Fill in the [TODO] sections with your analysis
  3. Make a decision: Proceed / Delay / Reject
  4. If proceeding, execute manually
```

The memo includes:
- Current weight: 20.5%
- Concentration flag noted
- All three investor lenses with prompts
- Template ready for analysis

### Example 2: Considering New Position

```bash
$ ./bin/investos decide --action new --name "Fairfax Financial" \
  --isin CA3039011026 --notes "Compounding machine at reasonable price"

✓ Decision memo created!
```

Memo structure same, but framed as "initiating new position"

## When to Create Decision Memos

**Required scenarios:**
- Before initiating new position
- Before significant position changes (>5% of portfolio)
- Reviewing concentrated positions (>10%)

**Recommended scenarios:**
- Quarterly portfolio review
- After significant market moves
- When thesis might have changed
- Periodic "do nothing" confirmation

**Not required for:**
- Routine rebalancing (mechanical)
- Tax loss harvesting (procedural)
- Tiny positions (<1% portfolio)

## Directory Structure

```
decisions/
├── YYYY-MM-DD_<isin>_<action>.md  # Individual decision memos
└── README.md                       # This file
```

Additional subdirectories (optional):
- `decisions/archive/` - Old decisions no longer relevant
- `decisions/reviews/` - Periodic portfolio reviews
- `decisions/post-mortems/` - Analysis of past decisions

## Measuring Decision Quality

Track decision outcomes:
1. Did I proceed, delay, or reject?
2. If proceeded, what happened?
3. What did I learn?
4. How would I decide differently now?

This feedback loop improves decision-making over time.

## Notes

- **NO TRADE EXECUTION** - System structures thinking, human executes
- **Explicit inaction** - "Hold" and "Delay" are valid decisions
- **Audit trail** - Git history shows all decisions and reasoning
- **Conservative bias** - When uncertain, favor inaction or smaller size
- **Thinking tool** - Helps you think, doesn't think for you

---

**Remember:** The memo is a tool for thinking, not a recommendation engine.
Fill it out honestly, and it will help you make better decisions.
