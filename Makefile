FILE := 01_the_impossible_dream.txt
VENV := .venv
REQUIREMENTS := requirements.txt
MAIN := main.py
INSTALL_STAMP := $(VENV)/.installed

$(VENV):
	python3 -m venv $(VENV)

$(INSTALL_STAMP): $(VENV) $(REQUIREMENTS)
	$(VENV)/bin/pip install -r $(REQUIREMENTS)
	touch $(INSTALL_STAMP)

install: $(INSTALL_STAMP)

run: install
	$(VENV)/bin/python3 $(MAIN) $(FILE)

debug: install
	$(VENV)/bin/python3 -m pdb $(MAIN) $(FILE)

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache

lint: install
	$(VENV)/bin/flake8 . --exclude=.venv
	$(VENV)/bin/mypy . --warn-return-any --warn-unused-ignores \
	--ignore-missing-imports --disallow-untyped-defs \
	--check-untyped-defs --exclude=.venv

lint-strict: install
	$(VENV)/bin/flake8 . --exclude=.venv
	$(VENV)/bin/mypy . --strict --exclude=.venv

.PHONY: install run debug clean lint lint-strict
