"""Testes de endpoints (rotas) usando TestClient.

Usa o mock_rag do conftest — não há chamada real ao Groq.
"""
from __future__ import annotations

from fastapi.testclient import TestClient


class TestRoot:
    def test_root_returns_status(self, client: TestClient) -> None:
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "RAG API running"
        assert "docs" in body


class TestHealth:
    def test_health_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["llm_ready"] is True
        assert body["retriever_ready"] is True


class TestQuery:
    def test_query_success(self, client: TestClient, mock_rag) -> None:
        """POST /query com pergunta válida retorna 200 + resposta."""
        resp = client.post("/query", json={"question": "Qual a conclusão?"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["answer"] == "Resposta simulada pelo mock."
        assert len(body["sources"]) == 1
        assert body["sources"][0]["page"] == 2
        assert body["elapsed_ms"] == 12.5

        # Confirma que o mock foi chamado com a pergunta certa
        mock_rag.initialize.assert_called_once()
        mock_rag.answer.assert_called_once_with("Qual a conclusão?")

    def test_query_short_question_rejected(self, client: TestClient) -> None:
        """Pergunta muito curta -> 422 (Pydantic rejeitou)."""
        resp = client.post("/query", json={"question": "oi"})
        assert resp.status_code == 422

    def test_query_empty_body_rejected(self, client: TestClient) -> None:
        """Body vazio -> 422."""
        resp = client.post("/query", json={})
        assert resp.status_code == 422

    def test_query_missing_field_rejected(self, client: TestClient) -> None:
        """Campo ausente -> 422."""
        resp = client.post("/query", json={"outra_coisa": "x"})
        assert resp.status_code == 422

    def test_query_oversized_question_rejected(self, client: TestClient) -> None:
        """Pergunta >1000 chars -> 422."""
        resp = client.post("/query", json={"question": "x" * 1001})
        assert resp.status_code == 422


class TestQueryErrors:
    def test_pdf_not_found_returns_503(self, client: TestClient, mock_rag) -> None:
        """Se o PDF sumir, resposta é 503 e não 500."""
        mock_rag.initialize.side_effect = FileNotFoundError("PDF ausente")
        resp = client.post("/query", json={"question": "teste válido"})
        assert resp.status_code == 503
        assert "PDF" in resp.json()["detail"] or "ausente" in resp.json()["detail"]

    def test_rag_not_ready_returns_503(self, client: TestClient, mock_rag) -> None:
        mock_rag.answer.side_effect = RuntimeError("não inicializado")
        resp = client.post("/query", json={"question": "teste válido"})
        assert resp.status_code == 503

    def test_unexpected_error_returns_500(self, client: TestClient, mock_rag) -> None:
        """Erros não previstos viram 500 com mensagem genérica."""
        mock_rag.answer.side_effect = Exception("boom")
        resp = client.post("/query", json={"question": "teste válido"})
        assert resp.status_code == 500
        # Mensagem genérica — não vaza stacktrace
        assert "boom" not in resp.json()["detail"]
