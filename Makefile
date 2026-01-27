.PHONY: help doctor test ingest validate value explain latest

help:
	@echo ""
	@echo "Investing OS — available commands:"
	@echo ""
	@echo "  make doctor                     Run health checks"
	@echo "  make test                       Run full test suite"
	@echo "  make ingest PDF=path ACCOUNT=x  Ingest Trade Republic PDF (ACCOUNT defaults to main)"
	@echo "  make latest                     Print latest snapshot path"
	@echo "  make validate SNAPSHOT=path     Validate snapshot against schema"
	@echo "  make value SNAPSHOT=path        Run valuation pipeline"
	@echo "  make explain FROM=A TO=B        Explain change between snapshots"
	@echo ""

doctor:
	./bin/investos doctor

test:
	python3 -m unittest -v

ingest:
	@if [ -z "$(PDF)" ]; then \
		echo "ERROR: PDF=path is required"; \
		exit 1; \
	fi
	./bin/investos ingest --pdf $(PDF) --account $(or $(ACCOUNT),main)

latest:
	@python3 -c "import glob, os; paths = sorted([p for p in glob.glob('portfolio/snapshots/*.json') if os.path.basename(p) != 'latest.json']); print(paths[-1] if paths else 'NO SNAPSHOTS')"

validate:
	@if [ -z "$(SNAPSHOT)" ]; then \
		echo "ERROR: SNAPSHOT=path is required"; \
		exit 1; \
	fi
	./bin/investos validate \
		--file $(SNAPSHOT) \
		--schema schema/portfolio-state.schema.json

value:
	@if [ -z "$(SNAPSHOT)" ]; then \
		echo "ERROR: SNAPSHOT=path is required"; \
		exit 1; \
	fi
	./bin/investos value --snapshot $(SNAPSHOT)

explain:
	@if [ -z "$(FROM)" ] || [ -z "$(TO)" ]; then \
		echo "ERROR: FROM=path and TO=path are required"; \
		exit 1; \
	fi
	./bin/investos explain --from $(FROM) --to $(TO)
