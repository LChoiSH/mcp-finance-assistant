"""Smoke tests for get_ecos_data MCP tool + 3-tool cross-reference check."""
from __future__ import annotations

import asyncio


def test_all_three_tools_registered():
    from server import mcp

    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    assert names == {
        "get_dart_disclosures",
        "search_research_reports",
        "get_ecos_data",
    }, f"got: {names}"


def test_descriptions_cross_reference_each_other():
    """All 3 tools must reference at least one sibling in their description."""
    from server import mcp

    tools = asyncio.run(mcp.list_tools())
    by_name = {t.name: t for t in tools}

    # disclosures should mention research + ecos
    d = by_name["get_dart_disclosures"].description or ""
    assert "search_research_reports" in d
    assert "get_ecos_data" in d

    # research should mention disclosures + ecos
    r = by_name["search_research_reports"].description or ""
    assert "get_dart_disclosures" in r
    assert "get_ecos_data" in r

    # ecos should mention disclosures + research
    e = by_name["get_ecos_data"].description or ""
    assert "get_dart_disclosures" in e
    assert "search_research_reports" in e
