.PHONY: dev demo eval test lint format

dev:
	uv run streamlit run src/amoa/ui/streamlit_app.py

demo:
	uv run python -m amoa.graph

eval:
	uv run python -m amoa.eval.harness

test:
	uv run pytest -v

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/
