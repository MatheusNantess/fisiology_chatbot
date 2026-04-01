import os
import re
from typing import List, Optional

from langchain_core.documents import Document
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

PART_PATTERN = re.compile(r"^Parte\s+\d+", re.IGNORECASE)
ONLY_NUMBER_PATTERN = re.compile(r"^\d+\s*$")


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\x00", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def detect_part_title(lines: List[str]) -> Optional[str]:
    for i, line in enumerate(lines[:10]):
        if PART_PATTERN.search(line):
            return " ".join(lines[i:i+3]).strip()
    return None


def detect_chapter_title(lines: List[str]) -> Optional[str]:
    for i, line in enumerate(lines[:10]):
        if ONLY_NUMBER_PATTERN.match(line):
            if i + 1 < len(lines):
                title = lines[i + 1].strip()
                if len(title) > 3:
                    return title
    return None


def extract_pages_with_metadata(
    pdf_path: str,
    start_page: int = 25,
    end_page: int = 848
) -> List[Document]:
    reader = PdfReader(pdf_path)
    documents = []

    current_part = None
    current_chapter = None

    last_page = min(end_page, len(reader.pages))

    for page_index in range(start_page - 1, last_page):
        raw_text = reader.pages[page_index].extract_text() or ""
        text = clean_text(raw_text)

        if not text:
            continue

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        detected_part = detect_part_title(lines)
        if detected_part:
            current_part = detected_part

        detected_chapter = detect_chapter_title(lines)
        if detected_chapter:
            current_chapter = detected_chapter

        doc = Document(
            page_content=text,
            metadata={
                "source": os.path.basename(pdf_path),
                "page": page_index + 1,
                "part_title": current_part,
                "chapter_title": current_chapter,
            },
        )
        documents.append(doc)

    return documents


def chunk_documents(
    documents: List[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = text_splitter.split_documents(documents)
    
    for chunk in chunks:
        context_header = []
        part = chunk.metadata.get("part_title")
        chapter = chunk.metadata.get("chapter_title")
        
        if part:
            context_header.append(f"Parte: {part}")
        if chapter:
            context_header.append(f"Capítulo: {chapter}")
            
        if context_header:
            context_str = " | ".join(context_header)
            chunk.page_content = f"[{context_str}]\n\n{chunk.page_content}"
            
    return chunks
