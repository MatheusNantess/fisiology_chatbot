import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag import extract_pages_with_metadata, chunk_documents
from app.vectorstore import create_or_load_vectorstore, CHROMA_PERSIST_DIR, buscar_com_rerank
import shutil

PDF_PATH = "data/livro.pdf"

if __name__ == "__main__":
    if os.path.exists(CHROMA_PERSIST_DIR):
        print(f"🗑️  Limpando banco vetorial antigo em {CHROMA_PERSIST_DIR}...")
        shutil.rmtree(CHROMA_PERSIST_DIR)

    print(f"1. Carregando PDF: {PDF_PATH}")
    docs = extract_pages_with_metadata(PDF_PATH, start_page=25, end_page=2000)

    print(f"2. Fazendo chunking de {len(docs)} páginas...")
    chunks = chunk_documents(docs, chunk_size=1000, chunk_overlap=200)
    print(f"--> {len(chunks)} chunks criados.")

    print("\n3. Vetorizando e gravando no ChromaDB...")
    vectorstore = create_or_load_vectorstore(documents=chunks)
    print("\n--> Banco vetorial gravado com sucesso!\n")

    # Smoke test
    test_query = "Qual a influência da Filosofia na Fisiologia grega e quem foi Hipócrates?"
    print(f"--- TESTE RAG COM RERANK ---")
    print(f"Query: '{test_query}'\n")

    results = buscar_com_rerank(vectorstore, test_query, k=10, top_n=2)

    for i, (res, score) in enumerate(results):
        print(f"🎖️  TOP {i + 1} | Score: {score:.4f}")
        print(f"Conteúdo: {res.page_content[:400]}...\n")
        print("-" * 60)
