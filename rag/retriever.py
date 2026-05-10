"""Retrieval over the Chroma-backed research reports index."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever

from rag.indexer import configure_settings, get_storage_context

log = logging.getLogger(__name__)


def get_retriever(top_k: int = 5, chroma_dir: Path | None = None) -> BaseRetriever:
    """Open the existing Chroma collection and return a retriever.

    The retriever does pure vector similarity — no LLM call path.
    """
    configure_settings()
    storage_context = get_storage_context(chroma_dir)
    index = VectorStoreIndex.from_vector_store(
        storage_context.vector_store,
        storage_context=storage_context,
    )
    return index.as_retriever(similarity_top_k=top_k)


def retrieve(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Convenience: run a query and return scored chunk dicts."""
    retriever = get_retriever(top_k=top_k)
    nodes = retriever.retrieve(query)
    log.info("retrieve %r → %d nodes", query, len(nodes))
    return [
        {
            "score": getattr(n, "score", None),
            "text": n.node.get_content(),
            "metadata": dict(n.node.metadata),
        }
        for n in nodes
    ]
