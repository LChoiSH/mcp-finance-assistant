"""Single source of truth for the embedding model.

Decisions.md §6: bge-m3 local model. To swap providers (OpenAI / Voyage / etc.)
change `get_embed_model` here — every other RAG module imports through this seam.

Note on imports: torch and HuggingFaceEmbedding are deferred into the function
bodies so module import stays cheap (~10ms vs ~25s eager). The heavy load only
happens the first time a tool actually needs an embedding.
"""
from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llama_index.core.embeddings import BaseEmbedding

EMBED_MODEL_NAME = "BAAI/bge-m3"


def _detect_device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


@lru_cache(maxsize=1)
def get_embed_model() -> "BaseEmbedding":
    """Return a process-wide cached embedding model.

    First call triggers a ~2.3GB model download to ~/.cache/huggingface/.
    Subsequent calls reuse the loaded model.
    """
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    return HuggingFaceEmbedding(
        model_name=EMBED_MODEL_NAME,
        device=_detect_device(),
    )
