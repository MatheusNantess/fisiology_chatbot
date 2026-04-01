import os
from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from app.vectorstore import create_or_load_vectorstore, buscar_com_rerank

# ================= ESTADO DO GRAFO ===================
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: str
    intent: str  # "chitchat" ou "academic"

# ================= LLM ===================
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1
)

# LLM mais "criativo" para respostas amigáveis
llm_friendly = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.8
)

# Inicializa o Vectorstore globalmente
vectorstore = create_or_load_vectorstore()

# ================= NÓS DO GRAFO ===================

def classify_node(state: AgentState):
    """Classifica a intenção da mensagem: chitchat ou academic."""
    messages = state.get("messages", [])
    if not messages:
        return {"intent": "chitchat"}

    last_message = messages[-1].content.strip()
    if not last_message:
        return {"intent": "chitchat"}

    prompt_classificador = f"""Você é um classificador de intenção de mensagens.
Analise a mensagem abaixo e responda APENAS com uma dessas duas palavras, sem explicações:

- "chitchat" → se a mensagem é: saudação, despedida, agradecimento, conversa casual, pergunta sobre você, elogio, reclamação geral, ou qualquer coisa que NÃO seja uma dúvida técnica ou acadêmica específica.
- "academic" → se a mensagem é: pergunta técnica, dúvida sobre fisiologia, anatomia, medicina, biologia, ou qualquer tema do conteúdo do curso.

Mensagem: "{last_message}"

Responda apenas: chitchat ou academic"""

    resposta = llm.invoke([HumanMessage(content=prompt_classificador)])
    intent = resposta.content.strip().lower()

    # Garante que só retorna valores válidos
    if "academic" in intent:
        return {"intent": "academic"}
    return {"intent": "chitchat"}


def route_by_intent(state: AgentState) -> Literal["friendly", "retrieve"]:
    """Edge condicional que decide o caminho baseado na intenção classificada."""
    return "friendly" if state.get("intent") == "chitchat" else "retrieve"


def friendly_node(state: AgentState):
    """Responde de forma humana e calorosa para conversas casuais — sem RAG."""
    messages = state.get("messages", [])

    prompt_amigavel = """Você é ProfeBot, um assistente virtual caloroso, simpático e bem-humorado de um portal educacional de Fisiologia.

Você tem uma personalidade amigável e acolhedora. Responda de forma natural, humana e próxima — como um colega especialista que também sabe bater papo.

REGRAS:
1. Nunca diga que é uma IA fria ou que não tem sentimentos. Aja como um assistente humano e presente.
2. Se cumprimentarem você, cumprimente de volta com entusiasmo e diga que está pronto para ajudar com Fisiologia.
3. Se agradecerem, responda com gentileza e incentive mais perguntas.
4. Se reclamarem, ouça com empatia e ofereça ajuda.
5. Respostas curtas e naturais — sem formalidade excessiva, sem "Prezado(a) aluno(a)".
6. Se a mensagem não tiver nada a ver com fisiologia, responda com simpatia e direcione gentilmente para o tema do portal."""

    mensagens_para_llm = [SystemMessage(content=prompt_amigavel)] + list(messages)
    resposta = llm_friendly.invoke(mensagens_para_llm)
    return {"messages": [resposta]}


def retrieve_node(state: AgentState):
    """Recupera contexto relevante do ChromaDB para perguntas acadêmicas."""
    messages = state.get("messages", [])
    if not messages:
        return {"context": ""}

    last_message = messages[-1].content
    resultados = buscar_com_rerank(vectorstore, last_message, k=25, top_n=6)
    contexto_formatado = "\n\n---\n\n".join(
        [f"[LITERAL DO LIVRO]:\n{doc.page_content}" for doc, _ in resultados]
    )
    return {"context": contexto_formatado}


def generate_node(state: AgentState):
    """Gera resposta acadêmica aprofundada com base no contexto RAG."""
    messages = state.get("messages", [])
    context = state.get("context", "")

    if not messages or not messages[-1].content.strip():
        return {"messages": [AIMessage(content="Por favor, digite uma pergunta válida.")]}

    prompt_sistema = f"""Você é o ProfeBot, um professor de Fisiologia brilhante, apaixonado pela área e com um dom natural para ensinar. Você é acessível, entusiasmado e profundamente conhecedor.

Sua missão é responder a dúvida acadêmica do aluno usando o material do livro como fonte primária, e seu conhecimento interno quando necessário.

REGRAS:
1. **PROFUNDIDADE**: Respostas completas, técnicas e detalhadas. Dignas de nota 10.
2. **FONTES**: Use o <material_de_apoio> como base. Se precisar expandir, use seu conhecimento — mas sinalize:
   - **[Fonte: Livro Base]** para informações do material
   - **[Fonte: Conhecimento Interno]** para seu conhecimento paramétrico
3. **TOM**: Seja um professor apaixonado, não um robô. Use analogias, exemplos clínicos, e entusiasmo pelo conteúdo.
4. **FORMATO**: Use Markdown (títulos, listas, negrito) para organizar bem a resposta.

<material_de_apoio>
{context}
</material_de_apoio>"""

    mensagens_para_llm = [SystemMessage(content=prompt_sistema)] + list(messages)
    resposta_direta = llm.invoke(mensagens_para_llm)
    return {"messages": [resposta_direta]}


# ================= ORQUESTRADOR ===================
workflow = StateGraph(AgentState)

# Adiciona todos os nós
workflow.add_node("classify", classify_node)
workflow.add_node("friendly", friendly_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)

# Fluxo: START → classify → (condicional) → friendly ou retrieve → generate → END
workflow.add_edge(START, "classify")

workflow.add_conditional_edges(
    "classify",
    route_by_intent,
    {
        "friendly": "friendly",
        "retrieve": "retrieve",
    }
)

workflow.add_edge("retrieve", "generate")
workflow.add_edge("friendly", END)
workflow.add_edge("generate", END)

# Compila o grafo base (sem checkpointer — o checkpointer é adicionado na API)
app_graph = workflow.compile()
