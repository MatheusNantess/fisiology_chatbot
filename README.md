# 🧠 ProfeBot — Agente RAG de Fisiologia com Memória Persistente

> Sistema de IA conversacional full-stack que combina **Retrieval-Augmented Generation (RAG)**, **roteamento condicional de intenção** e **memória persistente por usuário** — construído sobre LangGraph, Google Gemini, ChromaDB e Supabase.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-purple)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![Supabase](https://img.shields.io/badge/Supabase-Auth_+_PostgreSQL-green?logo=supabase)
![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-orange?logo=google)

---

## 📌 Visão Geral

O **ProfeBot** é um chatbot educacional inteligente voltado para estudantes de Fisiologia. Ele é capaz de:

- 📖 **Responder perguntas acadêmicas** com base em um livro-texto em PDF indexado via Embeddings + ChromaDB
- 💬 **Conversar humanamente** com o aluno em interações casuais (saudações, dúvidas, elogios)
- 🧠 **Lembrar toda a conversa** entre sessões — a memória persiste no PostgreSQL do Supabase
- 🔐 **Autenticar usuários** com Email e Senha via Supabase Auth
- ⚡ **Rotear inteligentemente** cada pergunta entre o pipeline RAG completo ou uma resposta amigável instantânea

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js 14)                   │
│   Tela de Login/Cadastro → Supabase Auth → Sala de Chat     │
│   React Markdown rendering · Dark Mode Glassmorphism UI     │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP POST /chat
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│   api/main.py · CORS · PostgresSaver Checkpointer          │
└──────────────────────────┬──────────────────────────────────┘
                           │ invoke(thread_id=user_uuid)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  GRAFO LANGGRAPH                             │
│                                                             │
│   START → [classify_node]                                   │
│               ├─ "chitchat" → [friendly_node] → END        │
│               └─ "academic" → [retrieve_node]               │
│                                   └─→ [generate_node] → END │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    [ChromaDB]      [Google Gemini]   [Supabase PG]
    Embeddings +    2.5 Flash LLM     PostgresSaver
    CrossEncoder    (RAG + Friendly)  (Memória Vitalícia)
    Reranking
```

---

## 🔀 Pipeline de Roteamento Condicional

Uma das funcionalidades centrais do projeto é o **roteamento dinâmico de intenção**.

O `classify_node` usa o próprio LLM para classificar cada mensagem do usuário:

| Tipo de Mensagem | Rota | Nó Destino |
|---|---|---|
| `"olá, tudo bem?"` | `chitchat` | `friendly_node` (sem RAG — resposta instantânea) |
| `"o que é pressão osmótica?"` | `academic` | `retrieve_node → generate_node` (pipeline RAG completo) |

Isso garante:
- ⚡ **Performance** — Saudações não consomem tempo do ChromaDB
- 🧑‍💼 **Humanização** — O bot não responde `"Prezado(a) aluno(a)"` para um simples "oi"
- 🔧 **Extensibilidade** — Fácil adicionar novas rotas (`complaint`, `billing`, `offtopic`)

---

## 🔍 Pipeline RAG com Reranking

```
Pergunta do usuário
       ↓
Embedding (intfloat/multilingual-e5-small)
       ↓
Busca Vetorial no ChromaDB (top-K=25 candidatos)
       ↓
Reranking semântico com CrossEncoder
(cross-encoder/mmarco-mMiniLMv2-L12-H384-v1)
       ↓
Top-N=6 chunks mais relevantes selecionados
       ↓
Injeção no System Prompt do Gemini
       ↓
Resposta gerada com citação de fonte:
  [Fonte: Livro Base] ou [Fonte: Conhecimento Interno]
```

---

## 🧠 Memória Persistente (PostgresSaver)

A memória **não é implementada via SQL Tool** — usa o sistema nativo de `Checkpointer` do LangGraph.

```python
# A cada invocação com o mesmo thread_id:
# 1. PostgresSaver carrega o state completo do banco ANTES da execução
# 2. O reducer add_messages faz merge: histórico + nova mensagem
# 3. O grafo executa com contexto completo
# 4. PostgresSaver salva o novo state APÓS a execução
config = {"configurable": {"thread_id": user_uuid}}
app_graph.invoke({"messages": [nova_mensagem]}, config=config)
```

Isso garante que cada usuário tenha sua própria árvore de conversa isolada no PostgreSQL, recuperada automaticamente no próximo login.

---

## 🗂️ Estrutura do Projeto

```
automacao_langgraph/
│
├── app/                        # Módulos do Agente LangGraph
│   ├── agent.py                # Grafo LangGraph (nós + roteamento condicional)
│   ├── vectorstore.py          # ChromaDB + Embeddings + CrossEncoder Reranker
│   └── rag.py                  # Pipeline auxiliar de processamento de PDF
│
├── api/                        # Servidor Backend
│   └── main.py                 # FastAPI + PostgresSaver + Rotas /chat e /history
│
├── frontend/                   # Interface Web (Next.js 14)
│   └── src/
│       ├── app/
│       │   ├── page.tsx        # Tela de Login / Cadastro (Supabase Auth)
│       │   └── chat/
│       │       └── page.tsx    # Sala de Chat com Markdown Rendering
│       └── lib/
│           └── supabase.ts     # Client Supabase configurado
│
├── data/                       # Livro PDF indexado + ChromaDB persistido
├── scripts/                    # Scripts de ingestão e testes
├── .env                        # Variáveis de ambiente (Python)
├── langgraph.json              # Config do LangGraph Studio
└── requirements.txt            # Dependências Python
```

---

## ⚙️ Stack Tecnológica

### Backend (Python)
| Tecnologia | Função |
|---|---|
| **LangGraph** | Orquestração do grafo de agente com roteamento condicional |
| **Google Gemini 2.5 Flash** | LLM principal para classificação, RAG e respostas amigáveis |
| **ChromaDB** | Banco de dados vetorial persistente |
| **intfloat/multilingual-e5-small** | Modelo de embeddings multilingual |
| **cross-encoder/mmarco-mMiniLMv2** | CrossEncoder para reranking semântico |
| **FastAPI** | API REST com CORS para servir o frontend |
| **langgraph-checkpoint-postgres** | PostgresSaver para memória persistente |
| **psycopg / psycopg-pool** | Driver PostgreSQL assíncrono |

### Frontend (TypeScript)
| Tecnologia | Função |
|---|---|
| **Next.js 14** | Framework React com App Router |
| **TailwindCSS** | Estilização utility-first |
| **Supabase JS** | Auth (Email/Senha) + client de banco |
| **react-markdown + remark-gfm** | Renderização de Markdown nas respostas |
| **lucide-react** | Biblioteca de ícones |

---

## 🚀 Como Rodar Localmente

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- Conta no [Supabase](https://supabase.com) (gratuita)
- Chave de API do [Google AI Studio](https://aistudio.google.com)

### 1. Clone e configure o ambiente Python

```bash
git clone https://github.com/seu-usuario/profebot-fisiologia.git
cd profebot-fisiologia

python -m venv .venv
.venv\Scripts\activate  # Windows

pip install langgraph langgraph-checkpoint-postgres langchain langchain-google-genai \
            chromadb sentence-transformers fastapi uvicorn psycopg psycopg-pool \
            psycopg-binary python-dotenv pydantic
```

### 2. Configure as variáveis de ambiente

Crie o arquivo `.env` na raiz:

```env
GOOGLE_API_KEY=sua_chave_google_ai
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_service_role_key
DATABASE_URL=postgresql://postgres:senha@db.seu-projeto.supabase.co:5432/postgres
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=sua_chave_langsmith  # Opcional, para observabilidade
```

Crie o arquivo `frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://seu-projeto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sua_anon_key_publica
```

> ⚠️ A `NEXT_PUBLIC_SUPABASE_ANON_KEY` é a chave **pública** (`anon`), diferente da `service_role`. Pegue em: Supabase Dashboard → Settings → API.

### 3. Indexe o livro PDF no ChromaDB

```bash
python scripts/ingest.py  # ou o script equivalente de ingestão
```

### 4. Inicie o Backend (Motor 1)

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Você verá: `🚀 API Iniciada. Conectado ao Supabase!`

### 5. Inicie o Frontend (Motor 2)

```bash
cd frontend
npm install
npm run dev
```

Acesse: **http://localhost:3000**

### 6. (Opcional) Visualize o Grafo no LangGraph Studio

```bash
# Na raiz do projeto:
langgraph dev
```

Acesse: **http://localhost:2024**

---

## 🔐 Autenticação

O sistema usa **Supabase Auth** com Email e Senha nativo.

- **Cadastro**: Novo usuário se registra com email + senha + confirmação de senha
- **Login**: Sessão JWT é gerenciada pelo Supabase automaticamente
- **Proteção de rota**: A página `/chat` valida a sessão via `supabase.auth.getSession()` e redireciona para `/` se não autenticado
- **UUID como Thread ID**: O UUID único do usuário no Supabase é usado como `thread_id` do LangGraph, garantindo isolamento total de memória

---

## 📊 Observabilidade

O projeto é integrado com **LangSmith** para rastreamento completo de cada execução do grafo:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT="RAG Fisiologia"
LANGCHAIN_API_KEY=sua_chave
```

No LangSmith você pode inspecionar:
- Qual intenção foi classificada (`chitchat` / `academic`)
- Quais chunks do livro foram recuperados e seus scores de reranking
- O prompt completo enviado ao Gemini
- Latência de cada nó do grafo

---

## 🎯 Diferenciais Técnicos

1. **Roteamento Condicional de Intenção** — O agente não é um pipeline linear. Ele decide dinamicamente entre resposta humanizada e RAG completo.

2. **Reranking com CrossEncoder** — Em vez de usar apenas a similaridade vetorial, aplicamos um modelo de reranking semântico em cima dos candidatos do ChromaDB, aumentando significativamente a relevância dos chunks.

3. **Checkpointer nativo vs SQL Tool** — A persistência de memória é feita via `PostgresSaver` (infraestrutura do LangGraph), não via tool SQL chamada pelo agente. Isso elimina pontos de falha e garante 100% de recuperação do histórico.

4. **Transparência de Fontes** — O modelo sinaliza explicitamente quando usa o livro (`[Fonte: Livro Base]`) vs. conhecimento paramétrico (`[Fonte: Conhecimento Interno]`).

5. **Injeção de Metadados Hierárquicos** — Os chunks são enriquecidos com metadados de `Part/Chapter` antes da indexação, preservando o contexto semântico do livro.

---

## 📄 Licença

MIT License — sinta-se livre para usar, modificar e distribuir.

---

<div align="center">
  <strong>Construído com LangGraph · Google Gemini · ChromaDB · Supabase · Next.js</strong>
</div>
