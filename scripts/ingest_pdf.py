import os
import sys

# Adiciona a raiz do projeto no PYTHONPATH para funcionar as importações de 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag import extract_pages_with_metadata, chunk_documents
from app.vectorstore import create_or_load_vectorstore, CHROMA_PERSIST_DIR, buscar_com_rerank
import shutil

PDF_PATH = "data/livro.pdf"

if __name__ == "__main__":
    # Limpa o banco antigo para evitar duplicatas se rodarmos o script várias vezes
    if os.path.exists(CHROMA_PERSIST_DIR):
        print(f"🗑️  Limpando o banco vetorial antigo ({CHROMA_PERSIST_DIR}) para evitar duplicação...")
        shutil.rmtree(CHROMA_PERSIST_DIR)

    print(f"1. Iniciando carregamento do PDF: {PDF_PATH}")
    
    # Agora vamos do início até o osso!
    docs = extract_pages_with_metadata(PDF_PATH, start_page=25, end_page=2000)
    
    print(f"2. Fazendo o Chunking Extremo de {len(docs)} páginas...")
    chunks = chunk_documents(docs, chunk_size=1000, chunk_overlap=200)
    print(f"--> {len(chunks)} chunks conscientes do contexto foram criados!")
    
    print("\n3. Iniciando processo de Vectorização no Banco...")
    # Essa etapa fará a mágica acontecer consumindo a CPu
    vectorstore = create_or_load_vectorstore(documents=chunks)
    print("\n--> Banco Vetorial gravado em disco com SUCESSO!\n")
    
    # --- SANITY TEST COM RERANKER ---
    # Nós testaremos buscar algo que a LLM precisaria saber e ver o VectorStore responder.
    test_query = "Qual a influência da Filosofia na Fisiologia grega e quem foi Hipócrates?"
    print(f"--- TESTANDO O RAG AVANÇADO (COM RERANK) ---")
    print(f"Pesquisa: '{test_query}'\n")
    
    # Distribui a busca customizada e manual implementada com o CrossEncoder
    results = buscar_com_rerank(vectorstore, test_query, k=10, top_n=2)
    
    print("\nAchei os Trechos Vencedores! Aqui estão os Pódios avaliados:\n")
    for i, (res, score) in enumerate(results):
        print(f"🎖️  TOP {i + 1} | Relevância (Score Rerank): {score:.4f}")
        print(f"Conteúdo: {res.page_content[:400]}...\n")
        print("-" * 60)
