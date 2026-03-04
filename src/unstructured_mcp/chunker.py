"""Chunking logic for RAG pipelines using Unstructured."""

import logging
import os
from dataclasses import dataclass, field

from .partitioner import partition

logger = logging.getLogger("unstructured-mcp")


@dataclass
class ChunkResult:
    chunks: list[dict] = field(default_factory=list)
    element_count: int = 0


def chunk(
    file_path: str,
    strategy: str = "auto",
    chunk_strategy: str = "by_title",
    max_characters: int = 1000,
    overlap: int = 200,
) -> ChunkResult:
    """Partition and chunk a document for RAG pipelines."""
    # First partition to get elements
    result = partition(file_path, strategy=strategy)
    elements = result.elements
    element_count = len(elements)

    if not elements:
        return ChunkResult(chunks=[], element_count=0)

    if chunk_strategy == "by_title":
        chunks = _chunk_by_title(elements, max_characters, overlap)
    else:
        chunks = _chunk_basic(elements, max_characters, overlap)

    logger.info(
        "Chunked %s: %d elements → %d chunks (strategy=%s, max=%d, overlap=%d)",
        os.path.basename(file_path),
        element_count,
        len(chunks),
        chunk_strategy,
        max_characters,
        overlap,
    )

    return ChunkResult(chunks=chunks, element_count=element_count)


def _chunk_by_title(elements: list[dict], max_chars: int, overlap: int) -> list[dict]:
    """Chunk by title/section boundaries — semantic chunking."""
    chunks = []
    current_texts: list[str] = []
    current_types: set[str] = set()
    current_length = 0
    current_title: str | None = None
    current_page: int | None = None

    for el in elements:
        el_type = el.get("type", "")
        text = el.get("text", "").strip()
        meta = el.get("metadata", {})
        page = meta.get("page_number")

        if not text:
            continue

        # Title starts a new chunk
        is_title = el_type in ("Title", "Header")
        would_overflow = current_length + len(text) > max_chars

        if (is_title or would_overflow) and current_texts:
            chunk_text = "\n\n".join(current_texts)
            chunks.append({
                "text": chunk_text,
                "char_count": len(chunk_text),
                "element_types": sorted(current_types),
                "section_title": current_title,
                "page_number": current_page,
            })

            # Apply overlap — carry tail text forward
            if overlap > 0 and chunk_text:
                overlap_text = chunk_text[-overlap:]
                current_texts = [overlap_text]
                current_length = len(overlap_text)
            else:
                current_texts = []
                current_length = 0
            current_types = set()

        if is_title:
            current_title = text
            current_page = page

        current_texts.append(text)
        current_types.add(el_type)
        current_length += len(text)
        if page and not current_page:
            current_page = page

    # Flush remaining
    if current_texts:
        chunk_text = "\n\n".join(current_texts)
        chunks.append({
            "text": chunk_text,
            "char_count": len(chunk_text),
            "element_types": sorted(current_types),
            "section_title": current_title,
            "page_number": current_page,
        })

    return chunks


def _chunk_basic(elements: list[dict], max_chars: int, overlap: int) -> list[dict]:
    """Fixed-size chunking with overlap."""
    full_text = "\n\n".join(el.get("text", "").strip() for el in elements if el.get("text"))
    chunks = []
    start = 0

    while start < len(full_text):
        end = start + max_chars
        chunk_text = full_text[start:end]

        chunks.append({
            "text": chunk_text,
            "char_count": len(chunk_text),
            "element_types": ["mixed"],
            "section_title": None,
            "page_number": None,
        })

        start = end - overlap if overlap < max_chars else end

    return chunks
