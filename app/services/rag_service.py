"""Serviço RAG central.

Carrega o PDF, indexa em FAISS, configura o LLM Groq e expõe um método
`answer(question)` que executa o pipeline completo.

O carregamento é preguiçoso: só roda na primeira chamada. Em testes,
pode ser substituído por mock sem nunca tocar no Groq.

Imports do LangChain são feitos dentro dos métodos (lazy import) para:
1. Reduzir tempo de boot do servidor (langchain é pesado)
2. Permitir que testes que usam mock não dependam de langchain instalado
3. Isolar falhas de dependência para o módulo que as usa
"""
from __future__ import annotations

import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.schemas.query import SourceChunk


class RagService:
    """Encapsula pipeline RAG: ingestão -> retriever -> LLM."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._qa_chain: Any = None
        self._retriever: Any = None
        self._llm: Any = None

    # ── Carregamento preguiçoso ──
    def initialize(self) -> None:
        """Carrega PDF, cria índice FAISS e instancia LLM.

        Idempotente: chamar mais de uma vez não refaz o trabalho.
        Levanta FileNotFoundError se o PDF não existir.
        """
        if self._qa_chain is not None:
            return

        logger.info("Inicializando RAG service...")
        start = time.perf_counter()

        documents = self._load_pdf()
        chunks = self._split_documents(documents)
        vectorstore = self._build_vectorstore(chunks)
        self._retriever = vectorstore.as_retriever(
            search_kwargs={"k": self.settings.retriever_k}
        )
        self._llm = self._build_llm()

        # Import lazy: só precisa do RetrievalQA quando realmente for usar
        from langchain.chains import RetrievalQA

        self._qa_chain = RetrievalQA.from_chain_type(
            llm=self._llm,
            retriever=self._retriever,
            return_source_documents=True,
        )

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "RAG service pronto em %.0f ms | chunks=%d k=%d",
            elapsed, len(chunks), self.settings.retriever_k,
        )

    # ── Pipeline de ingestão ──
    def _load_pdf(self) -> list[Any]:
        path: Path = self.settings.pdf_path
        if not path.exists():
            logger.error("PDF não encontrado: %s", path)
            raise FileNotFoundError(f"PDF não encontrado: {path}")
        logger.info("Carregando PDF: %s", path)

        # Import lazy
        from langchain_community.document_loaders import PyPDFLoader
        return PyPDFLoader(str(path)).load()

    def _split_documents(self, documents: list[Any]) -> list[Any]:
        # Import lazy
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        return splitter.split_documents(documents)

    def _build_vectorstore(self, chunks: list[Any]) -> Any:
        # Import lazy
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEmbeddings

        logger.info("Criando embeddings com %s", self.settings.embeddings_model)
        embeddings = HuggingFaceEmbeddings(
            model_name=self.settings.embeddings_model,
            model_kwargs={"trust_remote_code": True},
        )
        return FAISS.from_documents(chunks, embeddings)

    def _build_llm(self) -> Any:
        # Import lazy
        from langchain_groq import ChatGroq

        logger.info("Configurando LLM: %s", self.settings.groq_model)
        return ChatGroq(
            model=self.settings.groq_model,
            temperature=self.settings.llm_temperature,
            api_key=self.settings.groq_api_key,  # explícito para evitar KeyError
        )

    # ── API pública ──
    @property
    def is_ready(self) -> bool:
        return self._qa_chain is not None

    def answer(self, question: str) -> tuple[str, list[SourceChunk], float]:
        """Executa a chain QA e devolve (resposta, fontes, tempo_ms).

        Levanta RuntimeError se o serviço não foi inicializado.
        """
        if self._qa_chain is None:
            raise RuntimeError("RagService não inicializado — chame .initialize()")

        start = time.perf_counter()
        result = self._qa_chain.invoke({"query": question})
        elapsed_ms = (time.perf_counter() - start) * 1000

        answer_text: str = result["result"]
        sources = [
            SourceChunk(
                content=doc.page_content[:300],
                page=doc.metadata.get("page"),
            )
            for doc in result.get("source_documents", [])
        ]
        logger.info(
            "Query respondida em %.0f ms | sources=%d | q_len=%d",
            elapsed_ms, len(sources), len(question),
        )
        return answer_text, sources, elapsed_ms


# ── Instância singleton ──
@lru_cache(maxsize=1)
def get_rag_service() -> "RagService":
    """Injeta o RagService. Em testes, sobrescreva com dependency_overrides."""
    return RagService(get_settings())
