"""Configurações centralizadas via variáveis de ambiente.

Lê de .env ou do ambiente do sistema. Validado com Pydantic Settings,
então um valor inválido derruba o servidor no boot (falhar cedo).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da aplicação.

    Carrega .env da raiz do projeto automaticamente.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Aplicação ──
    app_name: str = "RAG API"
    app_version: str = "1.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # ── LLM (Groq) ──
    # Default vazio: a chave só é validada quando o RagService instancia
    # o ChatGroq. Assim, testes que usam mock não precisam de .env.
    groq_api_key: str = Field(
        default="",
        description="Chave de API do Groq Cloud (https://console.groq.com/keys)",
    )
    groq_model: str = "openai/gpt-oss-120b"
    llm_temperature: float = 0.2

    # ── Embeddings ──
    embeddings_model: str = "nomic-ai/nomic-embed-text-v1.5"

    # ── RAG ──
    pdf_path: Path = Field(
        default=Path("data/exemplo.pdf"),
        description="Caminho para o PDF usado como base de conhecimento",
    )
    chunk_size: int = 500
    chunk_overlap: int = 100
    retriever_k: int = 5

    # ── CORS ──
    cors_origins: list[str] = ["*"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cacheia a configuração — só lê o .env uma vez."""
    return Settings()
