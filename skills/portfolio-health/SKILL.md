---
name: portfolio-health
description: |
  Run system health checks to verify repository integrity, validate schemas,
  and identify broken snapshots. Use this skill when system behavior is
  unexpected, before running other operations, or when debugging issues.
  This is a read-only diagnostic skill that reports problems without fixing them.
allowed_tools:
  - Makefile:doctor
  - Bash:./bin/investos doctor
  - Bash:ls -la portfolio/snapshots/
  - Bash:ls -la schema/
inputs:
  - None: Health check runs automatically on current repository state
outputs:
  - health_status: Pass/fail with specific check results
  - warnings: List of non-critical issues found
  - errors: List of critical failures that block operations
artifacts:
  - logs/runs/YYYY-MM-DD/HHMMSS_doctor.json: Structured health check log
failure_modes:
  - missing_directories: Required directories don't exist
  - missing_schemas: Schema files not found or invalid
  - invalid_snapshots: JSON snapshots don't validate against schema
  - no_snapshots: portfolio/snapshots/ is empty
examples:
  - "Is my portfolio setup working correctly?"
  - "Check repository health"
  - "Verify system integrity before running analysis"
---

# SKILL: portfolio-health

## WHEN TO USE THIS SKILL

Use this skill when:
- Starting a new session or resuming work on repository
- User reports unexpected behavior or errors
- Before running complex operations (valuation, explanation)
- After repository setup or configuration changes
- User asks "is everything working?" or "check my setup"

Do NOT use this skill when:
- System is known to be healthy and user wants to proceed with analysis
- User asks about portfolio content (not system health)
- User wants to fix identified problems (doctor only diagnoses, doesn't fix)

## PRECONDITIONS

**Required:**
- Must be in repository root directory
- Repository must be git-initialized
- Basic directory structure should exist

**No data required:**
- Health check works even with no portfolio snapshots
- Reports what's missing rather than failing

## STEP-BY-STEP PROCEDURE

### Step 1: Run Health Check

**Using Makefile (PREFERRED):**
```bash
make doctor
```

**Using CLI directly:**
```bash
./bin/investos doctor
```

### Step 2: Read Output Carefully

Health check reports grouped into categories:

**✓ Pass indicators:**
- Green checkmarks or "✓" symbols
- Messages like "Schema validation: PASS"
- "Health check passed" summary

**✗ Fail indicators:**
- Red X marks or "✗" symbols
- "ERROR" or "CRITICAL" labels
- "Health check failed" summary

**⚠ Warning indicators:**
- Yellow warnings or "⚠" symbols
- "WARNING" labels
- Non-critical issues

### Step 3: Categorize Findings

**Example healthy output:**
```
Investment OS Health Check
==========================================================

Directory Structure:
  ✓ portfolio/raw exists
  ✓ portfolio/snapshots exists
  ✓ schema/ exists
  ✓ analysis/state exists
  ✓ decisions/ exists

Schemas:
  ✓ portfolio-state.schema.json valid
  ✓ valuation-model.schema.json valid
  ✓ decision-memo.schema.json valid

Portfolio Data:
  ✓ 15 snapshots found
  ✓ portfolio/latest.json points to valid snapshot
  ✓ Latest snapshot validates against schema

Configuration:
  ✓ config.json valid

==========================================================
Health check passed (0 errors, 0 warnings)
```

**Example with warnings:**
```
Portfolio Data:
  ✓ 15 snapshots found
  ⚠ 2 snapshots failed schema validation
    - portfolio/snapshots/2026-01-15-100000.json: missing required field 'totals'
    - portfolio/snapshots/2026-01-16-120000.json: invalid ISIN format
  ✓ Latest snapshot is valid

Health check passed (0 errors, 2 warnings)
```

**Example with errors:**
```
Directory Structure:
  ✗ portfolio/snapshots does not exist
  ✗ schema/ does not exist

Health check FAILED (2 errors, 0 warnings)
```

## VERIFICATION & SUCCESS CRITERIA

Health check succeeded if:

1. **Command exits with status 0**
2. **Summary says "Health check passed"**
3. **No critical errors reported**

Warnings are acceptable and don't fail the check.

## FAILURE HANDLING & RECOVERY

### Missing Directories (CRITICAL)
**Symptom:** "✗ <directory> does not exist"

**Recovery:**
1. Check if you're in repository root: `pwd`
2. Check git status: `git status`
3. If not in repo root, navigate there: `cd <repo_path>`
4. If directories truly missing, repository may be corrupted
5. Ask user: "Repository structure incomplete. Re-clone or run setup?"

**Do NOT:**
- Create directories automatically
- Assume directory locations
- Continue with other operations

### Missing Schemas (CRITICAL)
**Symptom:** "✗ <schema>.schema.json not found"

**Recovery:**
1. Verify you're in correct repository
2. Check schema/ directory: `ls schema/`
3. If schemas missing, repository is incomplete
4. Ask user: "Schema files missing. Re-clone repository?"

**Do NOT:**
- Generate schemas automatically
- Fetch schemas from external sources
- Proceed with operations that need schemas

### Invalid Snapshots (WARNING)
**Symptom:** "⚠ X snapshots failed schema validation"

**Recovery:**
1. Note which snapshots are broken (listed in output)
2. These snapshots are likely from old ingestion or manual editing
3. Inform user: "X old snapshots don't validate. Use latest snapshot instead."
4. Check if latest snapshot is valid
5. If latest is valid, operations can proceed

**Do NOT:**
- Attempt to fix broken snapshots automatically
- Delete invalid snapshots
- Block operations if latest snapshot is valid

### No Snapshots (WARNING/INFO)
**Symptom:** "⚠ No snapshots found" or "0 snapshots found"

**Recovery:**
1. This is expected for new repository setup
2. Inform user: "No portfolio data found. You need to ingest a PDF first."
3. Suggest: `make ingest PDF=<path>`

**Do NOT:**
- Treat this as an error
- Attempt to create empty snapshot
- Fetch data from external sources

### Configuration Invalid (ERROR)
**Symptom:** "✗ config.json invalid" or "config.json not found"

**Recovery:**
1. Check if config.json exists: `ls -la config.json`
2. Try to read it: `cat config.json`
3. If malformed JSON, report to user
4. Ask: "config.json is broken. Restore from git?"

**Do NOT:**
- Create new config.json
- Modify config.json automatically
- Guess configuration values

## FAILURE HANDLING BY SEVERITY

### CRITICAL (Blocks all operations)
- Missing directories
- Missing schema files
- Invalid config.json
- Repository not initialized

**Action:** Stop and ask user to fix setup.

### ERROR (Blocks some operations)
- Latest snapshot invalid
- All snapshots invalid
- Schema validation infrastructure broken

**Action:** Report to user, suggest re-ingestion.

### WARNING (Operations can proceed)
- Some old snapshots invalid
- No snapshots (new setup)
- Missing optional directories
- Non-critical config warnings

**Action:** Inform user, continue with operations.

## NOTES FOR AGENT REASONING

**Design Intent:**
Health check is a defensive diagnostic tool. Run it when uncertain about system state. It's designed to be fast (<1 second) and safe (read-only).

**What It Checks:**

1. **Directory Structure:**
   - All required directories exist
   - Permissions are correct
   - Git repository initialized

2. **Schema Files:**
   - All schema files present
   - Valid JSON syntax
   - Conform to JSON Schema Draft-07

3. **Portfolio Data:**
   - Snapshot files exist
   - Latest pointer is valid
   - Snapshots validate against schema
   - Counts and statistics

4. **Configuration:**
   - config.json exists and parses
   - Required fields present
   - Paths are valid

**What It Does NOT Check:**
- Portfolio content quality
- Market data accuracy
- Valuation correctness
- External system availability

**When to Run:**
- **Always:** When starting new session
- **Before:** Complex operations (explain, value)
- **After:** Repository changes or updates
- **During:** Debugging unexpected behavior

**Interpreting Results:**

**✓ All green:**
- System healthy
- Proceed with any operation

**⚠ Warnings only:**
- System mostly healthy
- Can proceed with caution
- Note warnings for later investigation

**✗ Any errors:**
- System unhealthy
- Fix errors before proceeding
- Do not attempt workarounds

**Common Patterns:**

**New repository:**
- Warnings about no snapshots (expected)
- Everything else should pass

**After git clone:**
- All checks should pass
- No snapshots is normal

**After manual edits:**
- May have invalid snapshots
- Latest should still be valid

**Composition with Other Skills:**

Health check is often the first step:
```
1. make doctor                  (verify system)
2. make ingest PDF=...         (if healthy)
3. make summarize              (if ingest succeeded)
4. make ask Q="..."            (if summary created)
```

**Conservative Approach:**
- Warnings are informational, not blocking
- Errors are blocking
- Never attempt automatic repairs
- Always ask user before fixing
- Report exactly what's wrong, don't interpret
