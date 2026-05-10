"""Smoke test for search_research_reports MCP tool.

Live retrieval requires:
    - PDFs indexed under data/chroma/ (run scripts/index_pdfs.py)
    - bge-m3 model downloaded (~2.3GB on first use)

Once both are present, manual verification via Inspector or Claude Desktop.
"""
from __future__ import annotations

import asyncio


def test_both_tools_registered():
    from server import mcp

    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    assert "search_research_reports" in names, f"got: {names}"
    assert "get_dart_disclosures" in names, f"got: {names}"


def test_research_tool_has_cross_references():
    """Description should point at sibling tools per Decisions.md §9."""
    from server import mcp

    tools = asyncio.run(mcp.list_tools())
    research = next(t for t in tools if t.name == "search_research_reports")
    desc = research.description or ""
    assert "get_dart_disclosures" in desc, "must redirect公시 queries"
    assert "get_ecos_data" in desc, "must redirect macro queries"
