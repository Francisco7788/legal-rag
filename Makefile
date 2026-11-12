.PHONY: install dev test test-cov lint format run clean help

help:  ## Mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Instala dependências de produção
	pip install -r requirements-base.txt

dev:  ## Instala dependências de desenvolvimento (inclui pytest, ruff)
	pip install -e ".[dev]"

run:  ## Inicia o servidor (com reload em dev)
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:  ## Roda os testes
	pytest

test-cov:  ## Roda testes com cobertura
	pytest --cov=app --cov-report=term-missing --cov-report=html

lint:  ## Verifica estilo (ruff)
	ruff check app tests

format:  ## Formata código (ruff)
	ruff format app tests
	ruff check --fix app tests

clean:  ## Remove artefatos (cache, coverage, etc)
	rm -rf __pycache__ .pytest_cache .ruff_cache .coverage htmlcov coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
