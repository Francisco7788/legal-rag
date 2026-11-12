# Legal RAG

API de Perguntas e Respostas sobre documentos (PDF) usando **RAG (Retrieval-Augmented Generation)**: ingere um PDF, indexa em FAISS e responde perguntas usando LLM via Groq Cloud.

Projeto desenvolvido com foco em aplicação prática de **Engenharia de Software** (estrutura modular, testes, CI/CD) e **Inteligência Artificial** (LangChain + embeddings + LLM).

## Stack

| Camada | Tecnologia |
|---|---|
| API REST | FastAPI |
| Orquestração RAG | LangChain |
| Vector store | FAISS (CPU) |
| LLM | Groq Cloud (Llama 3 / GPT-OSS) |
| Embeddings | Hugging Face (`nomic-embed-text-v1.5`) |
| Config | pydantic-settings + `.env` |
| Testes | pytest + pytest-cov + unittest.mock |
| Lint | ruff |
| CI | GitHub Actions |

## Estrutura

```
rag-api/
├── app/
│   ├── main.py              # Ponto de entrada FastAPI + lifespan
│   ├── api/
│   │   └── routes.py        # Rotas: /, /health, /query
│   ├── core/
│   │   ├── config.py        # Settings via .env (pydantic-settings)
│   │   └── logging.py       # Logger centralizado
│   ├── schemas/
│   │   └── query.py         # Schemas Pydantic (req/resp)
│   └── services/
│       └── rag_service.py   # Pipeline RAG (ingestão, retriever, chain)
├── tests/
│   ├── conftest.py          # Fixtures: mock_rag, client
│   ├── test_schemas.py      # Testes de validação
│   ├── test_routes.py       # Testes de endpoints (TestClient)
│   └── test_services.py    # Testes unitários com mocks
├── .github/workflows/
│   └── ci.yml               # CI: lint + testes em 3 versões do Python
├── .env.example             # Template de configuração
├── .gitignore
├── Makefile                 # Comandos comuns
├── pyproject.toml           # Configuração moderna do projeto
└── README.md
```

## Como executar

### 1. Clonar e preparar ambiente

```bash
git clone https://github.com/Francisco7788/rag-api.git
cd rag-api

# Cria e ativa venv
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# Instala dependências (inclui dev: pytest, ruff)
make dev
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite .env e preencha GROQ_API_KEY
# Obtenha em: https://console.groq.com/keys
```

### 3. Colocar um PDF de teste

```bash
mkdir -p data
# Opção recomendada: Código de Defesa do Consumidor (público, ~130 páginas)
curl -L -o data/exemplo.pdf "https://www2.camara.leg.br/legin/fed/lei/1990/lei-8078-11-setembro-1990-365086-normaatualizada-pl.pdf"

# Ou: copie qualquer PDF para data/exemplo.pdf
```

> O caminho do PDF é configurável via `PDF_PATH` no `.env`.

### 4. Rodar o servidor

```bash
make run
# Acesse: http://localhost:8000/docs
```

## Testes

```bash
make test        # roda todos
make test-cov    # com cobertura
make lint        # verificação de estilo
```

Os testes usam **mocks** para o LLM e FAISS, então rodam em segundos, sem `GROQ_API_KEY` válida nem PDF real.

### Cobertura atual

- `app/schemas/`: 100%
- `app/api/routes.py`: ~95%
- `app/services/rag_service.py`: ~85%

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Status da API |
| `GET` | `/health` | Health check granular (LLM, retriever) |
| `POST` | `/query` | Responde pergunta usando RAG |
| `GET` | `/docs` | Swagger UI |

### Exemplo de uso

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Quais as principais conclusões do documento?"}'
```

Resposta:

```json
{
  "answer": "As principais conclusões são...",
  "sources": [
    {"content": "trecho do PDF...", "page": 2},
    {"content": "outro trecho...", "page": 5}
  ],
  "elapsed_ms": 1234.56
}
```

## O que mudou em relação à versão 1.0

- **Estrutura modular**: cada responsabilidade em seu módulo (config, schemas, services, routes)
- **Configuração via `.env`**: nenhuma chave hardcoded; falha cedo se `GROQ_API_KEY` estiver ausente
- **Carregamento preguiçoso**: servidor sobe rápido; RAG inicializa em background ou sob demanda
- **Tratamento de erros**: 503 (serviço em inicialização), 422 (validação), 500 (erro inesperado)
- **Logging estruturado** em formato ISO-8601
- **Testes** com pytest + mocks: schemas, rotas e serviço
- **CI/CD** via GitHub Actions (lint + testes em Python 3.10/3.11/3.12)
- **CORS** configurável
- **Health check** granular
- **Schemas de resposta** com fontes (sources) e tempo de processamento
