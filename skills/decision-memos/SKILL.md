---
name: decision-memos
description: |
  Generate structured decision memos for capital allocation actions. This skill
  creates framework-driven documents that apply investor lenses to portfolio
  decisions. Memos structure thinking without making recommendations. All decisions
  require human judgment and manual execution. System never auto-executes trades.
allowed_tools:
  - Makefile:decide
  - Bash:./bin/investos decide --isin <isin> --action <action>
  - Bash:ls decisions/*.md
  - Bash:cat decisions/<memo>.md
inputs:
  - isin: Security ISIN (required for add/trim/exit, optional for new/hold)
  - action: Decision type (new/add/trim/exit/hold, default: hold)
  - name: Security name for new positions
  - notes: User context or reasoning
  - lens: Specific investor framework (marks/munger/klarman/all)
outputs:
  - decision_memo: Structured markdown file with analysis framework
  - portfolio_context: Current position size, concentration impact
  - lens_prompts: Questions from investor frameworks
artifacts:
  - decisions/YYYY-MM-DD_<isin>_<action>.md: Decision memo template
  - logs/runs/YYYY-MM-DD/HHMMSS_decide.json: Run log
failure_modes:
  - missing_isin: Required ISIN not provided for action that needs it
  - position_not_found: ISIN not in current portfolio (for add/trim/exit)
  - no_snapshot: No portfolio snapshot to extract context from
examples:
  - "Should I add to my Berkshire position?"
  - "Create decision memo for new position in Apple"
  - "Help me think through selling Microsoft"
---

# SKILL: decision-memos

## WHEN TO USE THIS SKILL

Use this skill when:
- User asks "should I buy/sell/hold?"
- User mentions considering a portfolio action
- User wants to think through a decision
- User asks for decision framework or structure
- User mentions specific security and action (buy, add, trim, exit)

Do NOT use this skill when:
- User wants current portfolio state (use portfolio-qa)
- User wants valuation (use portfolio-valuation)
- User wants to execute trade (not supported - human only)
- User just wants information about a security

## PRECONDITIONS

**Required:**
- Portfolio snapshot exists (for context)
- Repository validated (run `make doctor` if uncertain)

**Recommended:**
- Portfolio summary recent (run `make summarize`)
- Explanation available (if recent changes)

**Actions Explained:**

**new:** Initiating new position (ISIN optional, name helpful)
**add:** Adding to existing position (ISIN required)
**trim:** Reducing existing position (ISIN required)
**exit:** Closing existing position (ISIN required)
**hold:** Reviewing current position (ISIN optional)

## STEP-BY-STEP PROCEDURE

### Step 1: Identify Decision Parameters

**Ask user to clarify:**
- What security? (get ISIN if possible)
- What action? (new/add/trim/exit/hold)
- Any context? (why considering this?)

**Example clarification:**
```
User: "Should I buy more Apple?"
Agent: "I'll create a decision memo for adding to Apple (US0378331005).
        Do you have specific context or concerns to note?"
```

### Step 2: Run Decision Memo Generator

**Using Makefile (PREFERRED):**
```bash
make decide ISIN=<isin> ACTION=<action>
```

**Using CLI directly:**
```bash
./bin/investos decide --isin <isin> --action <action>
```

**Examples:**

**Review existing holding:**
```bash
make decide ISIN=US0378331005 ACTION=hold
./bin/investos decide --isin US0378331005
```

**Consider adding to position:**
```bash
make decide ISIN=US0378331005 ACTION=add
./bin/investos decide --isin US0378331005 --action add
```

**Consider new position:**
```bash
./bin/investos decide --action new --name "Costco Wholesale" --isin US22160K1051
```

**Consider trimming:**
```bash
./bin/investos decide --isin IE00B4L5Y983 --action trim \
  --notes "Position grew to 20% via appreciation"
```

**Consider exiting:**
```bash
./bin/investos decide --isin US6541061031 --action exit \
  --notes "Thesis broken - management change"
```

**Use specific lens:**
```bash
./bin/investos decide --isin US0846707026 --lens klarman
```

### Step 3: Read Output

**Expected console output:**
```
Creating decision memo...

Action: hold
ISIN: US0378331005
Lenses: marks, munger, klarman
Snapshot: latest.json

✓ Decision memo created!

Output: decisions/2026-01-29_US0378331005_hold.md

Next steps:
  1. Edit decisions/2026-01-29_US0378331005_hold.md
  2. Fill in the [TODO] sections with your analysis
  3. Make a decision: Proceed / Delay / Reject
  4. If proceeding, execute manually (system never auto-executes)
```

### Step 4: Guide User Through Memo

**Explain memo structure:**
```
The memo has 7 sections:

1. Decision Framing - What's being considered? (facts)
2. Portfolio Context - Current weight, concentration
3. Investor Lens Review - Marks/Munger/Klarman questions
4. Disconfirming Evidence - What would make this wrong?
5. Alternatives Considered - Do nothing, delay, etc.
6. Decision Status - Proceed/Delay/Reject checkboxes
7. Follow-ups - What to monitor, triggers to revisit

Fill in the [TODO] sections with your thinking.
```

### Step 5: Review Memo Location

```bash
ls -lh decisions/2026-01-29_<isin>_<action>.md
```

**Memo is ready for user to edit and complete.**

## VERIFICATION & SUCCESS CRITERIA

Decision memo succeeded if:

1. **Command exits with status 0**
2. **Memo file created** in decisions/
3. **All mandatory sections present**
4. **Portfolio context populated** (if position exists)
5. **Lens sections included**
6. **User notified** of next steps

## FAILURE HANDLING & RECOVERY

### Missing ISIN for Action Requiring It
**Symptom:** "Error: For 'add' action, must provide --isin"

**Recovery:**
1. Explain which actions need ISIN:
   - add, trim, exit require ISIN
   - new and hold optional
2. Ask user for ISIN
3. Suggest: "Find ISIN in portfolio snapshot or online"

**Do NOT:**
- Guess ISIN
- Look up ISIN without asking
- Proceed without required info

### Position Not Found (for add/trim/exit)
**Symptom:** "Warning: Position not found in current portfolio"

**Recovery:**
1. Memo still created (with warning noted)
2. Inform user: "This security isn't in your current portfolio"
3. For 'add': suggest 'new' action instead
4. For 'trim'/'exit': verify ISIN correct

**Do NOT:**
- Block memo creation
- Assume user is wrong
- Modify action automatically

### No Snapshot Available
**Symptom:** "✗ No portfolio snapshots found"

**Recovery:**
1. User needs to ingest data first
2. Suggest: `make ingest PDF=<path>`
3. Explain: "Decision memos need portfolio context"

**Do NOT:**
- Create memo without context
- Use old snapshot without asking
- Invent portfolio state

### Unclear User Intent
**Symptom:** User says "should I buy?" without specifics

**Recovery:**
1. Ask clarifying questions:
   - "Which security?"
   - "New position or adding to existing?"
   - "What's driving this consideration?"
2. Offer to create general review memo:
   ```bash
   ./bin/investos decide --action hold
   ```

**Do NOT:**
- Assume specific security
- Guess user's motivation
- Make recommendation

## DECISION MEMO STRUCTURE

Every memo includes these mandatory sections:

### 1. Decision Framing (Facts Only)
**What it contains:**
- Clear statement of decision being considered
- What changed (or didn't)
- What is known vs. unknown
- User context notes (if provided)

**Example:**
```markdown
**Decision:** Consider adding to existing position in Apple Inc.
**Current Weight:** 15.2%
**Recent Portfolio Change:** +21.6% since last snapshot

**Known:**
- Portfolio value: 193,666.76 EUR
- Current position: 29,450.00 EUR (15.2%)

**Unknown:**
- Current market conditions
- Future price movements
- Business fundamentals (use valuation separately)
```

### 2. Portfolio Context
**What it contains:**
- Current weight percentage
- Market value and quantity
- Concentration flags (other positions >10%)
- Recent portfolio drivers
- Correlation notes (manual analysis required)

### 3. Investor Lens Review
**What it contains:**
- Howard Marks questions (risk, cycles, what's priced in)
- Charlie Munger questions (understanding, incentives, moats)
- Seth Klarman questions (margin of safety, catalysts, liquidity)
- [TODO] markers for user to fill

### 4. Disconfirming Evidence
**What it contains:**
- What would make this decision wrong?
- What evidence would change mind?
- [TODO] markers for specific conditions

### 5. Alternatives Considered
**What it contains:**
- Do nothing (explicit evaluation)
- Reduce exposure elsewhere
- Delay decision
- Other options
- [TODO] markers for analysis

### 6. Decision Status
**What it contains:**
- Checkboxes: ☐ Proceed / ☐ Delay / ☐ Reject
- Rationale field (plain language)
- [TODO] marker for decision

### 7. Follow-ups & Triggers
**What it contains:**
- What should I monitor?
- What would force revisit?
- [TODO] markers for specifics

## LENS-SPECIFIC QUESTIONS

### Howard Marks Lens
**Focus:** Risk, cycles, second-level thinking

**Questions:**
- Where could permanent capital loss occur?
- What assumptions must be true?
- What's priced in? What does consensus believe?
- Where are we in cycle?
- How does this affect concentration?

### Charlie Munger Lens
**Focus:** Understanding, incentives, avoiding stupidity

**Questions:**
- Can I explain this business simply?
- Do I know how it makes money?
- Can I predict its state in 10 years?
- Where could I be fooling myself?
- What are management incentives?
- Is this simple or complex?

### Seth Klarman Lens
**Focus:** Margin of safety, value discipline, capital preservation

**Questions:**
- What protects me if I'm wrong?
- What's the downside case?
- What's my margin of safety?
- Am I investing or speculating?
- What's the catalyst?
- How liquid is this?

## NOTES FOR AGENT REASONING

**Design Intent:**
Decision memos are **thinking tools**, not recommendation engines. They structure judgment without making decisions.

**Human-in-the-Loop Always:**
- System creates framework
- Human fills analysis
- Human makes decision
- Human executes (if proceeding)
- System NEVER auto-executes

**No Recommendations:**
Memo never says:
- "You should buy"
- "This is undervalued"
- "Sell this position"
- "Good opportunity"

Memo asks:
- "What are the risks?"
- "Do you understand this?"
- "What could go wrong?"
- "What are alternatives?"

**Facts vs. Judgment:**

**Facts (populated automatically):**
- Current position size
- Portfolio concentration
- Recent changes
- Holdings count

**Judgment (user must fill):**
- Risk assessment
- Understanding level
- Margin of safety
- Decision rationale

**Template Nature:**
Memo is 80% template, 20% facts:
- Structure provided (sections, questions)
- Portfolio context auto-filled
- Analysis is [TODO] for user
- This is intentional - forces thinking

**Deterministic:**
Same portfolio + same ISIN + same action = same memo structure (excluding timestamps).

**What Gets Written:**
- **decisions/YYYY-MM-DD_<isin>_<action>.md:** Decision memo
- **logs/runs/:** Structured run log

**File Naming:**
```
2026-01-29_US0378331005_add.md    (adding to Apple)
2026-01-29_US0846707026_hold.md   (reviewing Berkshire)
2026-01-29_new_position_new.md    (considering new position)
```

**Composition with Other Skills:**

Typical decision workflow:
```
1. make summarize                        (understand current state)
2. make ask Q="Where is concentration?"  (identify considerations)
3. make decide ISIN=<ISIN> ACTION=<action>  (create memo)
4. [User fills memo manually]
5. [User decides: Proceed/Delay/Reject]
6. [User executes manually if Proceed]
7. make ingest PDF=<new_statement>       (after execution)
```

**When to Create Memos:**

**Required:**
- Before initiating new position
- Before significant changes (>5% portfolio)
- Reviewing concentrated positions (>10%)

**Recommended:**
- Quarterly portfolio review
- After significant market moves
- When thesis might have changed
- Periodic "hold" confirmation

**Not required:**
- Routine rebalancing (mechanical)
- Tax loss harvesting (procedural)
- Tiny positions (<1% portfolio)

**Explicit Inaction:**
"Hold" and "Delay" are valid outcomes:
- Hold: Maintaining position is deliberate
- Delay: Waiting for more information
- Both require rationale
- "Do nothing" is not lazy - it's a choice

**Conservative Approach:**
- Never push user toward action
- "Delay" and "Reject" are good outcomes
- Missing data → state explicitly
- Uncertainty → encourage caution
- User has final say always
