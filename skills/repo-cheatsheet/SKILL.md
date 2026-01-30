---
name: repo-cheatsheet
description: |
  Command index and workflow map for the Investment OS repository.
  Provides an agent with knowledge of all available high-level operations,
  their Makefile targets, CLI commands, and typical workflow sequences.
  Use this skill when you need to understand what operations are possible
  or how to compose multiple commands into a workflow.
allowed_tools:
  - Makefile:doctor
  - Makefile:ingest
  - Makefile:summarize
  - Makefile:explain
  - Makefile:value
  - Makefile:ask
  - Makefile:decide
  - Makefile:test
  - Makefile:latest
  - Bash:./bin/investos --help
inputs:
  - intent: User's stated goal or question about repository capabilities
outputs:
  - command_recommendation: Specific Makefile target or CLI command to use
  - workflow_sequence: Ordered list of commands if multiple steps needed
artifacts:
  - None: This is a read-only informational skill
failure_modes:
  - unclear_intent: User request doesn't map to available operations
  - missing_prerequisites: Required data (snapshots, summaries) don't exist
examples:
  - "Show me all available commands"
  - "What can I do with this portfolio?"
  - "How do I analyze my holdings?"
---

# SKILL: repo-cheatsheet

## WHEN TO USE THIS SKILL

Use this skill when:
- User asks "what can I do?" or "what commands are available?"
- User requests a workflow but you're uncertain which commands to use
- You need to understand the repository's capabilities before proceeding
- User asks about specific analysis types (valuation, risk, decision-making)

Do NOT use this skill when:
- User has already specified exact commands to run
- You're in the middle of executing a known workflow
- User asks for file content rather than command capabilities

## PRECONDITIONS

None. This skill is always available and requires no setup.

## COMMAND INVENTORY

### Core Operations

**System Health:**
```bash
make doctor
./bin/investos doctor
```
Verifies directory structure, schemas, and data integrity.

**Portfolio Ingestion:**
```bash
make ingest PDF=<path> ACCOUNT=<name>
./bin/investos ingest --pdf <path> --account <name>
```
Ingests Trade Republic PDF into canonical JSON snapshot.

**Portfolio Summary:**
```bash
make summarize
./bin/investos summarize
```
Creates deterministic portfolio state summary from latest snapshot.

**Portfolio Questions:**
```bash
make ask Q="<question>"
./bin/investos ask "<question>"
```
Answers portfolio questions using investor lenses (Marks/Munger/Klarman).

**Change Explanation:**
```bash
make explain FROM=<snapshot_A> TO=<snapshot_B>
./bin/investos explain --from <snapshot_A> --to <snapshot_B>
```
Explains mechanical portfolio changes between two snapshots.

**Valuation Analysis:**
```bash
make value SNAPSHOT=<path>
./bin/investos value --snapshot <path>
```
Runs offline, deterministic valuation analysis.

**Decision Memos:**
```bash
make decide ISIN=<isin> ACTION=<action>
./bin/investos decide --isin <isin> --action <action>
```
Creates structured decision memo for portfolio actions.

**Utilities:**
```bash
make latest
make test
```

## TYPICAL WORKFLOW SEQUENCES

### 1. New Portfolio Statement Arrived
```
1. make ingest PDF=~/Downloads/statement.pdf ACCOUNT=main
2. make summarize
3. make ask Q="What changed that deserves attention?"
```

### 2. Reviewing Existing Portfolio
```
1. make summarize  (if not recent)
2. make ask Q="Where is my biggest risk?"
3. make decide ISIN=<isin> ACTION=hold  (for specific positions)
```

### 3. Considering New Position
```
1. make summarize
2. make ask Q="Where is concentration risk?"
3. make decide ACTION=new --name "Company Name"
```

### 4. Understanding Recent Changes
```
1. Find previous snapshot: make latest
2. make explain FROM=<old> TO=<new>
3. make ask Q="What drove these changes?"
```

### 5. Running Valuations
```
1. make value SNAPSHOT=portfolio/latest.json
2. Review warnings about missing fundamentals
3. Optional: Fill fundamentals in valuations/inputs/
4. Re-run valuation
```

## VERIFICATION & SUCCESS CRITERIA

Success means:
- Agent identifies the correct command(s) for user's intent
- Agent explains what the command will do
- Agent identifies any missing prerequisites
- Agent suggests workflow order if multiple steps needed

## FAILURE HANDLING & RECOVERY

**If user intent is unclear:**
- Ask clarifying questions
- List 2-3 most likely workflows
- Example: "Are you trying to ingest new data, analyze existing portfolio, or make a decision?"

**If prerequisites are missing:**
- Identify what's missing (e.g., "No portfolio snapshots found")
- Suggest the prerequisite command first
- Example: "Before analyzing, you need to ingest data: make ingest PDF=..."

**If no suitable command exists:**
- Explain what operations ARE available
- Ask if user can rephrase their goal
- Do NOT invent capabilities that don't exist

## NOTES FOR AGENT REASONING

**Design Intent:**
This skill serves as the "front door" to the Investment OS. An agent should consult this when uncertain about capabilities or workflow ordering.

**Conservative Approach:**
- Always prefer Makefile targets over raw CLI commands (shorter, documented)
- Always suggest `make doctor` if system state is uncertain
- Always suggest `make summarize` before `make ask` or `make decide`

**Composition Pattern:**
Most workflows follow: **ingest → summarize → analyze → decide**
- Ingest brings data in
- Summarize creates queryable state
- Analyze applies thinking (ask, explain, value)
- Decide creates structured memos

**What This Skill Does NOT Do:**
- Does not execute commands (other skills do that)
- Does not make recommendations about what to analyze
- Does not interpret results
- Does not access external data

Use this skill as a "routing table" to dispatch to more specific skills.
