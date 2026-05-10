"""Centralized configuration: .env loading and shared paths.

Tools/clients import from here instead of reading os.environ directly,
so the boundary with the outside world is one file.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# httpx logs the full request URL at INFO, which includes API keys in the
# query string. We have our own DART client log that omits the key, so silence
# httpx/httpcore noise globally.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

PROJECT_ROOT = Path(__file__).parent.resolve()

DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
CHROMA_DIR = DATA_DIR / "chroma"
CACHE_DB = DATA_DIR / "cache.db"

DART_API_KEY = os.getenv("DART_API_KEY")
ECOS_API_KEY = os.getenv("ECOS_API_KEY")


def require(name: str, value: str | None) -> str:
    if not value:
        raise RuntimeError(
            f"{name} is not set. Provide it one of these ways:\n"
            f"  • Local clone: copy .env.example to .env and fill in {name}\n"
            f"  • MCP client (Claude Code / Desktop): add an 'env' field to the\n"
            f"    server entry in your MCP config (e.g. \"env\": {{\"{name}\": \"...\"}})\n"
            f"  • Shell: export {name}=... before launching the MCP client"
        )
    return value
