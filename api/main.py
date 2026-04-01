import os
import sys

# Garante que o Python consegue enxergar a pasta 'app' importando tudo a partir da raiz do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Carrega as variáveis do .env (como DATABASE_URL)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from app.agent import workflow
from langchain_core.messages import HumanMessage, AIMessage

# Recupera o link poderoso do Supabase
DB_URI = os.getenv("DATABASE_URL")
if not DB_URI:
    raise ValueError("A variável DATABASE_URL não foi encontrada no arquivo .env!")

# Criação do Pool de conexões do Banco de Dados
pool = ConnectionPool(conninfo=DB_URI, max_size=20)

# O Checkpointer precisa instalar tabelas na primeira vez. 
# Para evitar o erro do "CREATE INDEX CONCURRENTLY inside transaction", usamos conexao com autocommit
with pool.connection() as conn:
    conn.autocommit = True
    PostgresSaver(conn).setup()

# O Checkpointer definitivo que vai operar normalmente usando transações do Pool
checkpointer = PostgresSaver(pool)

# Aqui nós re-compilamos o Robô (workflow base), mas agora acoplando a Memória do Postgres
app_graph_persistente = workflow.compile(checkpointer=checkpointer)

# Contexto de vida útil do Servidor (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 API Iniciada. Conectado ao Supabase!")
    yield
    print("🛑 Encerrando conexões com Banco de Dados...")
    pool.close()

# O Servidor FastAPI
app = FastAPI(title="Chatbot API Fisiologia", lifespan=lifespan)

# Libera o acesso para o React no frontend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Na produção, coloque a URL exata do seu Next.js ou Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Objeto que vai receber os dados do React
class MensagemRequest(BaseModel):
    user_id: str
    thread_id: str
    message: str

@app.get("/chat/history/{thread_id}")
def get_history(thread_id: str):
    """
    Quando o aluno logar (abre o chat), o React pede todo o histórico pra preencher a tela.
    O get_state recupera a árvore de memória exata do PostgresSaver!
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        estado = app_graph_persistente.get_state(config)
        
        historico = []
        if estado and estado.values and "messages" in estado.values:
            for msg in estado.values["messages"]:
                historico.append({
                    "role": "user" if msg.type in ["human", "user"] else "bot",
                    "content": msg.content
                })
        return {"status": "success", "history": historico}
    except Exception as e:
        print("❌ Erro ao buscar histórico:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat_endpoint(request: MensagemRequest):
    """
    Rota responsável por cruzar o React com LangGraph.
    - Recebe o ID do aluno e o ID da conversa.
    - O checkpointer resgata todas as perguntas do passado daquele ID.
    - Roda o RAG Reranker + LLM.
    - Atualiza a linha no Supabase.
    - Devolve o resultado textual.
    """
    try:
        # Configuração nativa do Langgraph para persistir as conversas isoladamente
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # Embala a pergunta num formato que a LangChain entende
        nova_mensagem = HumanMessage(content=request.message)
        
        print(f"📡 Disparando RAG para o Thread: {request.thread_id}")
        
        # Como o checkpointer cuida de buscar o passado no PostgreSQL, 
        # a gente só precisa enviar essa NOVIDADE de agora pro invoke (reducer 'add_messages' fará a fusão)
        resultado = app_graph_persistente.invoke({"messages": [nova_mensagem]}, config=config)
        
        # A última folha da árvore de mensagens é sempre a resposta
        resposta_final = resultado["messages"][-1].content
        
        return {
            "status": "success",
            "reply": resposta_final
        }
    except Exception as e:
        print("❌ Erro no RAG:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
