"""ChromaDB-backed retrieval over USCIS O-1A guidance PDFs.

Public surface:
- `ingest_legal_docs()` — read every PDF under data/legal_docs/, chunk it,
  and upsert into a persistent Chroma collection.
- `retrieve_context(query, k)` — return concatenated top-k chunks for prompt
  augmentation, or None if the collection is empty.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings
from pypdf import PdfReader

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEGAL_DOCS_DIR = PROJECT_ROOT / "data" / "legal_docs"
DEFAULT_CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"
COLLECTION_NAME = "o1a_legal_docs"

CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 150


@dataclass
class Chunk:
    text: str
    source: str
    chunk_index: int

    @property
    def id(self) -> str:
        digest = hashlib.sha1(f"{self.source}:{self.chunk_index}:{self.text[:64]}".encode()).hexdigest()
        return digest[:24]


def _client(persist_dir: Path) -> chromadb.api.ClientAPI:
    persist_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False, allow_reset=False),
    )


def _collection(persist_dir: Path = DEFAULT_CHROMA_DIR):
    client = _client(persist_dir)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: List[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as exc:  # pragma: no cover - defensive against malformed PDFs
            logger.warning("Failed to extract a page from %s: %s", path.name, exc)
    return "\n".join(pages)


def _chunk_text(text: str, source: str) -> List[Chunk]:
    text = " ".join(text.split())  # normalize whitespace
    if not text:
        return []
    chunks: List[Chunk] = []
    step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
    idx = 0
    for start in range(0, len(text), step):
        piece = text[start : start + CHUNK_SIZE]
        if not piece.strip():
            continue
        chunks.append(Chunk(text=piece, source=source, chunk_index=idx))
        idx += 1
        if start + CHUNK_SIZE >= len(text):
            break
    return chunks


def ingest_legal_docs(
    legal_docs_dir: Path = DEFAULT_LEGAL_DOCS_DIR,
    persist_dir: Path = DEFAULT_CHROMA_DIR,
) -> tuple[int, int]:
    """Ingest every PDF under `legal_docs_dir`. Returns (files_processed, chunks_added)."""
    legal_docs_dir.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(legal_docs_dir.glob("*.pdf"))
    if not pdfs:
        logger.warning("No PDFs found in %s", legal_docs_dir)
        return 0, 0

    collection = _collection(persist_dir)
    existing_ids = set(collection.get(include=[]).get("ids", []))

    files_processed = 0
    chunks_added = 0
    for pdf_path in pdfs:
        logger.info("Ingesting %s", pdf_path.name)
        try:
            text = _read_pdf(pdf_path)
        except Exception as exc:
            logger.error("Failed to read %s: %s", pdf_path.name, exc)
            continue
        chunks = _chunk_text(text, source=pdf_path.name)
        if not chunks:
            continue
        new_chunks = [c for c in chunks if c.id not in existing_ids]
        if new_chunks:
            collection.upsert(
                ids=[c.id for c in new_chunks],
                documents=[c.text for c in new_chunks],
                metadatas=[
                    {"source": c.source, "chunk_index": c.chunk_index} for c in new_chunks
                ],
            )
            chunks_added += len(new_chunks)
        files_processed += 1
    return files_processed, chunks_added


def collection_size(persist_dir: Path = DEFAULT_CHROMA_DIR) -> int:
    try:
        return _collection(persist_dir).count()
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not read collection size: %s", exc)
        return 0


def retrieve_context(
    query: str,
    k: int = 5,
    persist_dir: Path = DEFAULT_CHROMA_DIR,
) -> Optional[str]:
    """Return concatenated top-k chunks for the query, or None if nothing is indexed."""
    if not query.strip():
        return None
    collection = _collection(persist_dir)
    if collection.count() == 0:
        return None
    # Chroma needs query text length to be reasonable; truncate to keep embedding fast.
    truncated = query[:4000]
    results = collection.query(query_texts=[truncated], n_results=k)
    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0]
    if not docs:
        return None
    blocks = []
    for doc, meta in zip(docs, metas):
        src = (meta or {}).get("source", "unknown")
        blocks.append(f"[source: {src}]\n{doc}")
    return "\n\n---\n\n".join(blocks)


def num_retrieved(context: Optional[str]) -> int:
    if not context:
        return 0
    return context.count("[source: ")


# Allow running `python -m backend.rag` to ingest from the CLI for local setup.
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    files, chunks = ingest_legal_docs()
    print(f"Ingested {chunks} chunks from {files} PDFs into {DEFAULT_CHROMA_DIR}")
