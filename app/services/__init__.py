"""Serviços de RAG: ingestão de PDF, embeddings, retriever, chain QA.

Cada serviço é uma classe com init + método. Mantidos separados das rotas
para que possam ser testados isoladamente (e substituídos por mocks).
"""
from __future__ import annotations

from app.services.rag_service import RagService, get_rag_service

__all__ = ["RagService", "get_rag_service"]
