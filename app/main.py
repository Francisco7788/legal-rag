"""Ponto de entrada da aplicação FastAPI.

Define lifespan (carrega RAG em background), middleware CORS e roteador.
Para rodar: `uvicorn app.main:app --reload`
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import logger
from app.services.rag_service import get_rag_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carrega o RAG na inicialização do servidor.

    Em produção isso bloqueia o boot por ~10-30s (download de embeddings).
    Em testes, o lifespan pode ser desativado para não carregar nada.
    """
    logger.info("Iniciando %s v%s", settings.app_name, settings.app_version)
    rag = get_rag_service()
    try:
        rag.initialize()
        logger.info("Aplicação pronta para receber requisições")
    except Exception as e:
        logger.warning(
            "RAG não carregou no boot (%s). Será inicializado sob demanda.",
            e,
        )
    yield
    logger.info("Encerrando aplicação")


app = FastAPI(
    title=settings.app_name,
    description="API de Perguntas e Respostas usando RAG (LLM + FAISS + Groq)",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
