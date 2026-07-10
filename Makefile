.PHONY: install test lint fmt run

install:
	pip install -r requirements.txt

test:
	pytest -q

lint:
	ruff check .

fmt:
	ruff format .

run:
	uvicorn app:app --reload