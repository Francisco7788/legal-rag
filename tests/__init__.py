"""Pacote de testes.

Estrutura:
- conftest.py     -> fixtures compartilhadas (client, mock_rag)
- test_schemas.py -> validação dos schemas Pydantic
- test_routes.py  -> testes de endpoints com TestClient
- test_services.py-> testes unitários do RagService com mocks

Rodar: pytest -v --cov=app --cov-report=term-missing
"""
