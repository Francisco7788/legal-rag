"""Testes de schemas: validação de entrada e serialização.

Estes testes são rápidos (sem IO) e garantem que a camada Pydantic
protege a API de entradas inválidas antes de tocar o LLM.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.query import QueryRequest, QueryResponse, SourceChunk


class TestQueryRequest:
    def test_valid_question(self) -> None:
        req = QueryRequest(question="Quais as conclusões do relatório?")
        assert req.question == "Quais as conclusões do relatório?"

    def test_short_question_rejected(self) -> None:
        """Perguntas com menos de 3 caracteres são inválidas."""
        with pytest.raises(ValidationError):
            QueryRequest(question="oi")

    def test_empty_question_rejected(self) -> None:
        with pytest.raises(ValidationError):
            QueryRequest(question="")

    def test_oversized_question_rejected(self) -> None:
        """Perguntas >1000 caracteres gastariam muitos tokens."""
        with pytest.raises(ValidationError):
            QueryRequest(question="x" * 1001)


class TestQueryResponse:
    def test_serialization(self) -> None:
        resp = QueryResponse(
            answer="Resposta",
            sources=[SourceChunk(content="ctx", page=1)],
            elapsed_ms=42.5,
        )
        assert resp.answer == "Resposta"
        assert len(resp.sources) == 1
        assert resp.elapsed_ms == 42.5

    def test_default_sources_empty(self) -> None:
        resp = QueryResponse(answer="x", elapsed_ms=1.0)
        assert resp.sources == []


class TestSourceChunk:
    def test_page_optional(self) -> None:
        chunk = SourceChunk(content="texto")
        assert chunk.page is None

    def test_with_page(self) -> None:
        chunk = SourceChunk(content="texto", page=5)
        assert chunk.page == 5
