import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag import extract_pages_with_metadata, chunk_documents

PDF_PATH = "data/livro.pdf"

docs = extract_pages_with_metadata(PDF_PATH, start_page=25, end_page=848)
chunks = chunk_documents(docs, chunk_size=1000, chunk_overlap=200)

print(f"Total de páginas processadas: {len(docs)}")
print(f"Total de chunks gerados: {len(chunks)}")
print("-" * 80)

for chunk in chunks[:5]:
    print(chunk.metadata)
    print(chunk.page_content[:500])
    print("=" * 80)