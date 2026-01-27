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
```