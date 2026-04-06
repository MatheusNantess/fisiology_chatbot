import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from app.agent import workflow
from langchain_core.messages import HumanMessage, AIMessage

DB_URI = os.getenv("DATABASE_URL")
if not DB_URI:
    raise ValueError("A variável DATABASE_URL não foi encontrada no arquivo .env!")

pool = ConnectionPool(conninfo=DB_URI, max_size=20)

# Setup precisa rodar com autocommit para evitar erro do CREATE INDEX CONCURRENTLY dentro de transação
with pool.connection() as conn:
    conn.autocommit = True
    PostgresSaver(conn).setup()

checkpointer = PostgresSaver(pool)
app_graph_persistente = workflow.compile(checkpointer=checkpointer)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 API Iniciada. Conectado ao Supabase!")
    yield
    print("🛑 Encerrando conexões com Banco de Dados...")
    pool.close()


app = FastAPI(title="Chatbot API Fisiologia", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MensagemRequest(BaseModel):
    user_id: str
    thread_id: str
    message: str


@app.get("/chat/history/{thread_id}")
def get_history(thread_id: str):
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
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        nova_mensagem = HumanMessage(content=request.message)

        print(f"📡 Disparando RAG para o Thread: {request.thread_id}")

        resultado = app_graph_persistente.invoke({"messages": [nova_mensagem]}, config=config)
        resposta_final = resultado["messages"][-1].content

        return {
            "status": "success",
            "reply": resposta_final
        }
    except Exception as e:
        print("❌ Erro no RAG:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
