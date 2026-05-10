"""RAG smoke tests — imports and device detection only.

Real indexing/retrieval requires:
    - PDFs in data/pdfs/
    - bge-m3 model (~2.3GB, auto-downloaded on first embed call)

Both are exercised by the user via:
    uv run python scripts/index_pdfs.py
once PDFs are placed in data/pdfs/.
"""
from __future__ import annotations


def test_rag_modules_import():
    import rag.embedding  # noqa: F401
    import rag.indexer    # noqa: F401
    import rag.retriever  # noqa: F401


def test_device_detection_returns_known_device():
    from rag.embedding import _detect_device

    assert _detect_device() in ("mps", "cuda", "cpu")


def test_build_index_returns_zero_with_empty_pdf_dir(tmp_path):
    """No PDFs → no indexing call, no model download triggered."""
    from rag.indexer import build_index

    pdfs = tmp_path / "pdfs"
    pdfs.mkdir()
    chroma = tmp_path / "chroma"

    n = build_index(pdf_dir=pdfs, chroma_dir=chroma)
    assert n == 0
