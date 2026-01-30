# Investing OS — Cheatsheet (v1)

## Setup (first time)
```bash
python3 -m venv .venv  
source .venv/bin/activate  
python3 -m pip install -r requirements.txt  
```

## Health + tests
```bash
./bin/investos doctor  
python3 -m unittest -v  
```

## Ingest Trade Republic PDF → snapshot
```bash
./bin/investos ingest --pdf ~/Downloads/<file>.pdf --account main
```

## Validate a snapshot against schema
```bash
./bin/investos validate \
  --file portfolio/snapshots/<snapshot>.json \
  --schema schema/portfolio-state.schema.json  
```

## Value a snapshot (offline; emits scaffolds if missing)
```bash
./bin/investos value \
  --snapshot portfolio/snapshots/<snapshot>.json \
  --profile conservative \
  --emit-scaffolds  
```

## Explain changes between two snapshots
```bash
./bin/investos explain \
  --from portfolio/snapshots/<A>.json \
  --to portfolio/snapshots/<B>.json  
```

## Portfolio Analysis (Step 7)

### Create portfolio summary
```bash
./bin/investos summarize
```

### Ask portfolio questions
```bash
# General questions
./bin/investos ask "What should I pay attention to?"
./bin/investos ask "Where is my biggest risk?"

# Risk-focused (Howard Marks lens)
./bin/investos ask "What would Howard Marks worry about?"
./bin/investos ask "Where could I lose money permanently?"

# Understanding-focused (Charlie Munger lens)
./bin/investos ask "Do I understand these businesses?"
./bin/investos ask "Where are my psychological blind spots?"

# Value-focused (Seth Klarman lens)
./bin/investos ask "Where is my margin of safety?"
./bin/investos ask "Am I investing or speculating?"
```

## Decision Memos (Step 8)

### Create decision memo
```bash
# Review existing position
./bin/investos decide --isin US0378331005

# Consider adding to position
./bin/investos decide --isin US0378331005 --action add

# Consider new position
./bin/investos decide --action new --name "Costco" --isin US22160K1051

# Consider trimming
./bin/investos decide --isin IE00B4L5Y983 --action trim

# With context notes
./bin/investos decide --isin US0846707026 --action hold \
  --notes "Reviewing after recent 20% gain"
```

## Find newest snapshot quickly
```bash
python3 - <<'PY'
import glob, os
paths = sorted([
    p for p in glob.glob("portfolio/snapshots/*.json")
    if os.path.basename(p) != "latest.json"
])
print(paths[-1] if paths else "NO SNAPSHOTS")
PY
```

## Makefile shortcuts (recommended)

```bash
make help  
make doctor  
make test  

make ingest PDF=~/Downloads/file.pdf  
make latest  

make validate SNAPSHOT=portfolio/snapshots/<file>.json  
make value SNAPSHOT=portfolio/snapshots/<file>.json  

make explain FROM=portfolio/snapshots/A.json TO=portfolio/snapshots/B.json

make summarize
make ask Q="What should I pay attention to?"
make decide ISIN=US0378331005 ACTION=hold
```