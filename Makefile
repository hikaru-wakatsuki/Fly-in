FILE := input_file.txt
VENV := .venv
REQUIREMENTS := requirements.txt
MAIN := main.py
INSTALL_STAMP := $(VENV)/.installed

$(VENV):			python3 -m venv $(VENV)

$(INSTALL_STAMP): 	$(VENV) $(REQUIREMENTS)
					pip install -r $(REQUIREMENTS)
					touch $(INSTALL_STAMP)

install:			$(INSTALL_STAMP)

run:				install
					source $(VENV)/bin/activate \
					&& python3 $(MAIN) $(FILE)

debug:				install
					source $(VENV)/bin/activate \
					&& python3 -m pdb $(MAIN) $(FILE)

clean:
					rm -rf $(VENV)

lint:				install
					$(VENV)/bin/flake8 .
					$(VENV)/bin/mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:		install
					$(VENV)/bin/flake8 .
					$(VENV)/bin/mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

.PHONY: install run debug clean lint lint-strict
