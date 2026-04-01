import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag import extract_pages_with_metadata

PDF_PATH = "data/livro.pdf"

docs = extract_pages_with_metadata(PDF_PATH, start_page=25, end_page=120)

last_part = None
last_chapter = None

for doc in docs:
    part = doc.metadata.get("part_title")
    chapter = doc.metadata.get("chapter_title")
    page = doc.metadata.get("page")

    # Verifica se a Parte ou o Capítulo mudaram nesta página
    if part != last_part or chapter != last_chapter:
        print(f"Página {page} -> Parte: {part} | Capítulo: {chapter}")
        print(doc.page_content[:150].replace('\n', ' ') + "...")
        print("-" * 80)
        last_part = part
        last_chapter = chapter