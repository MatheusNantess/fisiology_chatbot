import sys
import os
from dotenv import load_dotenv

# Injeta imediatamente a API Key do Groq presente em .env
load_dotenv()

# Adiciona a raiz do projeto no PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent import app_graph
from langchain_core.messages import HumanMessage

if __name__ == "__main__":
    print("=========================================================")
    print("      🧪 CHAT COM O PROFESSOR DE FISIOLOGIA (LLaMA 3 70B)")
    print("=========================================================")
    print("Digite sua dúvida e deixe o Professor usar o Reranker para elaborar!")
    print("As LPU (Chips) do Groq na Nuvem vão responder a velocidade da luz.\nDigite 'sair' para fechar.")

    historico = []

    while True:
        try:
            user_input = input("\n👤 Você: ")
        except (EOFError, KeyboardInterrupt):
            break
            
        if user_input.lower().strip() in ["sair", "exit", "quit", "q"]:
            break
            
        if not user_input.strip():
            continue
            
        # Adicionamos a fala humana no chat persistente nosso
        historico.append(HumanMessage(content=user_input))
        
        print("\n⏳ Professor buscando, reranqueando e digitando...\n")
        
        # Ativa o Grafo passando o histórico de estado! Ele bate primeiro no Retrieve_Node, depois Generate_Node.
        estado_inicial = {"messages": historico}
        estado_final = app_graph.invoke(estado_inicial)
        
        # Extrai a fala da máquina da lista mágica que ele retornou
        resposta_agente = estado_final["messages"][-1]
        
        print(f"👨‍🏫 Professor: {resposta_agente.content}\n")
        
        # Guarda na memória temporal para que a proxima conversa não seja avulsa
        historico.append(resposta_agente)
