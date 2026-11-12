"""Schemas Pydantic para request e response da API.

Validação de entrada é a primeira camada de defesa: uma pergunta vazia
nunca deve chegar ao LLM (gasta tokens e retorna erro genérico).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Corpo da requisição POST /query."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Pergunta em linguagem natural sobre o documento",
        examples=["Quais são as principais conclusões do relatório?"],
    )


class SourceChunk(BaseModel):
    """Trecho recuperado do vector store usado como contexto."""

    content: str = Field(..., description="Conteúdo do chunk")
    page: int | None = Field(default=None, description="Página de origem no PDF")


class QueryResponse(BaseModel):
    """Resposta da API."""

    answer: str = Field(..., description="Resposta gerada pelo LLM")
    sources: list[SourceChunk] = Field(
        default_factory=list,
        description="Trechos do documento usados como contexto",
    )
    elapsed_ms: float = Field(..., description="Tempo total de processamento (ms)")


class HealthResponse(BaseModel):
    """Resposta do endpoint /health."""

    status: str
    version: str
    llm_ready: bool
    retriever_ready: bool
