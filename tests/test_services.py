"""Testes unitários do RagService.

Estes testes usam mocks para isolar a lógica de orquestração das chamadas
reais ao Groq / FAISS / HuggingFace. Validam que o serviço:
- carrega o PDF quando o caminho existe
- levanta FileNotFoundError quando o PDF não existe
- repassa a pergunta para a chain corretamente
- formata as fontes (sources) como esperado

Como o serviço usa lazy imports (imports dentro dos métodos), e o ambiente
de teste pode não ter langchain instalado, criamos stubs de módulos via
sys.modules e patch.object com create=True.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.schemas.query import SourceChunk
from app.services.rag_service import RagService


def make_settings(pdf_path: str | Path = "data/exemplo.pdf") -> Settings:
    """Settings de teste — não precisa de .env real."""
    return Settings(
        groq_api_key="fake-key-for-tests",
        pdf_path=Path(pdf_path),
    )


@pytest.fixture(autouse=True)
def stub_langchain_modules():
    """Registra módulos LangChain stub em sys.modules.

    Permite que testes rodem sem langchain instalado. Os patches individuais
    substituem as classes dentro desses stubs.
    """
    needed = [
        "langchain",
        "langchain.chains",
        "langchain_community",
        "langchain_community.document_loaders",
        "langchain_community.vectorstores",
        "langchain_core",
        "langchain_core.documents",
        "langchain_groq",
        "langchain_huggingface",
        "langchain_text_splitters",
    ]
    created = []
    for mod_name in needed:
        if mod_name not in sys.modules:
            sys.modules[mod_name] = types.ModuleType(mod_name)
            created.append(mod_name)

    # Adiciona classes stub
    lc_loader = sys.modules["langchain_community.document_loaders"]
    lc_vs = sys.modules["langchain_community.vectorstores"]
    lc_groq = sys.modules["langchain_groq"]
    lc_hf = sys.modules["langchain_huggingface"]
    lc_chain = sys.modules["langchain.chains"]
    lc_splitter = sys.modules["langchain_text_splitters"]

    lc_loader.PyPDFLoader = MagicMock()  # type: ignore[attr-defined]
    lc_vs.FAISS = MagicMock()  # type: ignore[attr-defined]
    lc_groq.ChatGroq = MagicMock()  # type: ignore[attr-defined]
    lc_hf.HuggingFaceEmbeddings = MagicMock()  # type: ignore[attr-defined]
    lc_chain.RetrievalQA = MagicMock()  # type: ignore[attr-defined]
    lc_splitter.RecursiveCharacterTextSplitter = MagicMock()  # type: ignore[attr-defined]

    yield

    # Limpa apenas o que criamos
    for mod_name in created:
        sys.modules.pop(mod_name, None)


class TestRagServiceInit:
    def test_initialize_raises_when_pdf_missing(self, tmp_path: Path) -> None:
        """PDF inexistente -> FileNotFoundError antes de qualquer import."""
        missing_pdf = tmp_path / "nao_existe.pdf"
        service = RagService(make_settings(pdf_path=missing_pdf))

        with pytest.raises(FileNotFoundError, match="PDF não encontrado"):
            service.initialize()

    def test_initialize_full_pipeline(self, tmp_path: Path) -> None:
        """Fluxo completo com todas as dependências mockadas."""
        pdf_file = tmp_path / "doc.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        from langchain_community.document_loaders import PyPDFLoader as mock_loader
        from langchain_community.vectorstores import FAISS as mock_faiss
        from langchain_groq import ChatGroq as mock_groq
        from langchain_huggingface import HuggingFaceEmbeddings as mock_embed
        from langchain.chains import RetrievalQA as mock_chain_cls

        mock_loader.return_value.load.return_value = [
            MagicMock(page_content="conteúdo", metadata={"page": 0})
        ]
        mock_vs = MagicMock()
        mock_faiss.from_documents.return_value = mock_vs
        mock_chain_cls.from_chain_type.return_value = MagicMock()

        service = RagService(make_settings(pdf_path=pdf_file))
        service.initialize()

        # Verifica encadeamento: loader foi chamado com o path certo
        mock_loader.assert_called_once_with(str(pdf_file))
        mock_embed.assert_called_once()
        mock_groq.assert_called_once()
        assert service.is_ready is True

    def test_initialize_idempotent(self, tmp_path: Path) -> None:
        """Chamar initialize() duas vezes não refaz o trabalho."""
        pdf_file = tmp_path / "doc.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        from langchain_community.document_loaders import PyPDFLoader as mock_loader
        from langchain_community.vectorstores import FAISS as mock_faiss

        mock_loader.return_value.load.return_value = [
            MagicMock(page_content="x", metadata={"page": 0})
        ]
        mock_faiss.from_documents.return_value = MagicMock()

        service = RagService(make_settings(pdf_path=pdf_file))
        service.initialize()
        service.initialize()  # segunda chamada — não deve refazer

        assert mock_loader.call_count == 1


class TestRagServiceAnswer:
    def test_answer_without_init_raises(self) -> None:
        service = RagService(make_settings())
        with pytest.raises(RuntimeError, match="não inicializado"):
            service.answer("pergunta?")

    def test_answer_calls_chain_and_formats(self) -> None:
        """answer() formata resposta e fontes corretamente."""
        service = RagService(make_settings())
        # Injeta mock direto no atributo privado (já inicializado)
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {
            "result": "Resposta do LLM",
            "source_documents": [
                MagicMock(page_content="trecho 1", metadata={"page": 1}),
                MagicMock(page_content="trecho 2", metadata={"page": 3}),
            ],
        }
        service._qa_chain = mock_chain  # type: ignore[attr-defined]

        answer, sources, elapsed = service.answer("pergunta?")

        assert answer == "Resposta do LLM"
        assert len(sources) == 2
        assert sources[0].page == 1
        assert isinstance(sources[0], SourceChunk)
        assert elapsed >= 0
        mock_chain.invoke.assert_called_once_with({"query": "pergunta?"})
