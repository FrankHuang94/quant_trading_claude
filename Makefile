# Quant Trading KB - common tasks. Use `make PY=/path/to/python` to pick an interpreter.
PY ?= python3
MKDOCS ?= $(PY) -m mkdocs
LABS := $(sort $(wildcard labs/[0-9][0-9]-*/lab.py))

.PHONY: help site serve labs labs-smoke walkthroughs check check-strict wordcount matrix sources lint

help:
	@echo "make site | serve | labs | labs-smoke | walkthroughs | check | check-strict | wordcount | matrix | sources | lint"

site:
	$(MKDOCS) build --strict

serve:
	$(MKDOCS) serve

labs:
	$(PY) scripts/run_labs.py

labs-smoke:
	$(PY) scripts/run_labs.py --smoke --max-seconds 60

walkthroughs:
	$(PY) scripts/run_labs.py --walkthroughs

check:
	$(PY) scripts/fix_dollars.py --check
	$(PY) scripts/check_template.py --quiet
	$(PY) scripts/check_matrix.py
	$(PY) scripts/check_glossary_links.py
	$(PY) scripts/wordcount.py
	$(MKDOCS) build --strict --quiet

check-strict:
	$(PY) scripts/fix_dollars.py --check
	$(PY) scripts/check_template.py --strict --quiet
	$(PY) scripts/check_matrix.py
	$(PY) scripts/check_glossary_links.py --strict
	$(PY) scripts/wordcount.py
	$(MKDOCS) build --strict --quiet

wordcount:
	$(PY) scripts/wordcount.py

matrix:
	$(PY) scripts/check_matrix.py --write

sources:
	$(PY) scripts/build_sources.py

lint:
	npx --yes markdownlint-cli2@0.17.2 "docs/**/*.md" "*.md" "labs/**/*.md"
