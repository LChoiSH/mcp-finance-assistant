"""One-shot indexer: read data/pdfs/*.pdf → embed → write to data/chroma/.

Usage:
    uv run python scripts/index_pdfs.py

First run downloads bge-m3 (~2.3GB) to ~/.cache/huggingface/.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a script.
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.indexer import build_index  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-5s %(name)-22s %(message)s",
)


if __name__ == "__main__":
    n = build_index()
    print(f"\nIndexed {n} document(s).")
