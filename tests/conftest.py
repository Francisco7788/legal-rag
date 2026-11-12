"""Fixtures compartilhadas.

A fixture `client` sobe a FastAPI via TestClient SEM carregar o LLM real
(substituído por mock). Isso permite rodar todos os testes em <2s,
sem Groq API key, sem PDF, sem download de embeddings.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.rag_service import get_rag_service
from app.schemas.query import SourceChunk


@pytest.fixture
def mock_rag() -> MagicMock:
    """Mock do RagService. Não toca em LLM, PDF nem FAISS."""
    rag = MagicMock()
    rag.is_ready = True
    rag.initialize.return_value = None
    rag.answer.return_value = (
        "Resposta simulada pelo mock.",
        [SourceChunk(content="trecho 1", page=2)],
        12.5,
    )
    return rag


@pytest.fixture
def client(mock_rag: MagicMock) -> TestClient:
    """TestClient com RagService substituído por mock.

    Importante: dependency_overrides é limpo no fim da fixture.
    """
    app.dependency_overrides[get_rag_service] = lambda: mock_rag
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
