"""Rotas da API: /health, /, /query.

Cada rota é uma função async. Erros esperados viram HTTPException com
código e mensagem apropriados — nunca deixamos o cliente receber 500
sem explicação.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.logging import logger
from app.schemas.query import HealthResponse, QueryRequest, QueryResponse
from app.services.rag_service import RagService, get_rag_service

router = APIRouter()


@router.get("/", tags=["meta"])
def root() -> dict:
    """Root endpoint — confirma que a API está rodando."""
    return {"status": "RAG API running", "docs": "/docs"}


@router.get("/health", response_model=HealthResponse, tags=["meta"])
def health(rag: RagService = Depends(get_rag_service)) -> HealthResponse:
    """Health check com indicadores granulares."""
    return HealthResponse(
        status="ok" if rag.is_ready else "starting",
        version="1.1.0",
        llm_ready=rag.is_ready,
        retriever_ready=rag.is_ready,
    )


@router.post("/query", response_model=QueryResponse, tags=["rag"])
def query(
    request: QueryRequest,
    rag: RagService = Depends(get_rag_service),
) -> QueryResponse:
    """Responde pergunta sobre o documento usando RAG.

    Fluxo: valida entrada (Pydantic) -> inicializa RAG se necessário ->
    invoca chain -> retorna resposta + fontes + tempo.

    Erros:
    - 503: serviço ainda inicializando
    - 500: erro inesperado no pipeline
    """
    try:
        rag.initialize()
    except FileNotFoundError as e:
        logger.error("PDF ausente: %s", e)
        raise HTTPException(
            status_code=503,
            detail=f"Documento base não disponível: {e}",
        ) from e

    try:
        answer, sources, elapsed_ms = rag.answer(request.question)
    except RuntimeError as e:
        logger.error("RAG não pronto: %s", e)
        raise HTTPException(status_code=503, detail="Serviço em inicialização") from e
    except Exception as e:
        logger.exception("Falha inesperada ao processar query")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar a pergunta",
        ) from e

    return QueryResponse(
        answer=answer,
        sources=sources,
        elapsed_ms=round(elapsed_ms, 2),
    )
