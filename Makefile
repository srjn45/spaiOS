PYTHON := uv run python
UV := uv

.PHONY: install lint format test run clean

install:
	$(UV) sync

lint:
	$(UV) run flake8 src/ --max-line-length=100

format:
	$(UV) run black src/

format-check:
	$(UV) run black src/ --check

test:
	$(UV) run pytest tests/ -v

run:
	$(UV) run python src/main.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .venv dist build *.egg-info
