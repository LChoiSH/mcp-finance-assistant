"""LlamaIndex pipeline: PDFs → chunks → bge-m3 embeddings → Chroma."""
from __future__ import annotations

import logging
from pathlib import Path

import chromadb
from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.vector_stores.chroma import ChromaVectorStore

from config import CHROMA_DIR, PDF_DIR
from rag.embedding import get_embed_model

log = logging.getLogger(__name__)

CHROMA_COLLECTION = "research_reports"
# Per Plan.md risk table: smaller chunks for Korean text quality.
CHUNK_SIZE = 512
CHUNK_OVERLAP = 100


def configure_settings() -> None:
    """Wire embed model into LlamaIndex Settings, disable default LLM."""
    Settings.embed_model = get_embed_model()
    Settings.llm = None
    Settings.chunk_size = CHUNK_SIZE
    Settings.chunk_overlap = CHUNK_OVERLAP


def get_storage_context(chroma_dir: Path | None = None) -> StorageContext:
    path = chroma_dir or CHROMA_DIR
    path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(path))
    collection = client.get_or_create_collection(name=CHROMA_COLLECTION)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    return StorageContext.from_defaults(vector_store=vector_store)


def build_index(
    pdf_dir: Path | None = None,
    chroma_dir: Path | None = None,
) -> int:
    """Read every PDF in pdf_dir, chunk + embed, write to Chroma. Returns doc count."""
    pdf_dir = pdf_dir or PDF_DIR
    pdfs = list(pdf_dir.glob("*.pdf"))
    if not pdfs:
        log.warning("No PDFs found in %s — nothing to index", pdf_dir)
        return 0

    log.info("Loading %d PDFs from %s", len(pdfs), pdf_dir)
    configure_settings()

    documents = SimpleDirectoryReader(
        input_dir=str(pdf_dir),
        required_exts=[".pdf"],
    ).load_data()
    log.info("Loaded %d source documents", len(documents))

    storage_context = get_storage_context(chroma_dir)
    VectorStoreIndex.from_documents(documents, storage_context=storage_context)
    log.info("Index built: %d documents → Chroma collection %r", len(documents), CHROMA_COLLECTION)
    return len(documents)
