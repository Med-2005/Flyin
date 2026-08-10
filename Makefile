PYTHON = python3
PIP = pip3
MAP ?= setting.txt


install:
	@$(PIP) install flake8 mypy

run:
	@$(PYTHON) main.py $(MAP)

debug:
	@$(PYTHON) -m pdb main.py $(MAP)

clean:
	@rm -rf __pycache__
	@rm -rf .mypy_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete

lint:
	@flake8 .
	@mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
