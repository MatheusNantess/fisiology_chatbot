import sys
import os

# Adiciona a raiz do projeto no PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.vectorstore import create_or_load_vectorstore, buscar_com_rerank

if __name__ == "__main__":
    print("Iniciando o carregamento do Banco Vetorial (Isso pode demorar alguns segundos na primeira vez se estiver lendo do disco)...")
    
    # Ao chamar sem documents=None, ele Apenas Carrega o banco existente
    vectorstore = create_or_load_vectorstore()
    print("Banco e Modelos HuggingFace carregados com sucesso!\n")
    
    print("=========================================================")
    print("      TESTE INTERATIVO DO RAG (BUSCA + RERANK)           ")
    print("=========================================================")
    print("Faça perguntas naturais sobre Fisiologia. Digite 'sair' para fechar.")

    while True:
        try:
            query = input("\n🤖 Sua Pergunta: ")
        except (EOFError, KeyboardInterrupt):
            break
            
        if query.lower().strip() in ["sair", "exit", "quit", "q"]:
            break
            
        if not query.strip():
            continue
            
        print("⏳ Buscando as 10 passagens matemáticas mais próximas e acionando o modelo Reranker para julgar as 3 melhores...")
        
        # Nossa função customizada que faz o trabalho braçal de Ranqueamento Humanoide
        resultados = buscar_com_rerank(vectorstore, query, k=10, top_n=3)
        
        print("\n" + "▼"*80)
        for i, (doc, nota) in enumerate(resultados):
            pagina = doc.metadata.get("page", "Desconhecida")
            
            # Agora a "nota" já é enviada como probabilidade (0.0 a 1.0) devido ao nosso Sigmoid no vectorstore.py
            print(f"🏆 [{i + 1}º Lugar] | Confiança do Reranker: {nota * 100:.1f}% | Origem: Página {pagina}")
            
            # Printa o trecho recuperado INTEIRO, sem cortes
            print(f"📜 Conteúdo Original na Íntegra:\n{doc.page_content.strip()}\n")
            print("-" * 80)
        print("▲"*80)
