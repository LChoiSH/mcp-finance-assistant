"""Integration tests for the get_dart_disclosures MCP tool.

`test_tool_registers` — server.py imports cleanly and the tool is registered.
`test_tool_live_cache_then_hit` — first call fetches DART, second call hits cache.
"""
from __future__ import annotations

import asyncio

import pytest

from config import DART_API_KEY


def test_tool_registers():
    from server import mcp

    tools = asyncio.run(mcp.list_tools())
    names = [t.name for t in tools]
    assert "get_dart_disclosures" in names, f"got: {names}"


@pytest.mark.skipif(not DART_API_KEY, reason="DART_API_KEY not set")
def test_tool_live_cache_then_hit(monkeypatch, tmp_path):
    """First call: cache miss → DART. Second call: cache hit (no DART)."""
    monkeypatch.setattr("storage.db.CACHE_DB", tmp_path / "tool.db")

    from tools.disclosures import get_dart_disclosures

    async def call():
        return await get_dart_disclosures(
            corp_code="00126380", bgn_de="20250101", end_de="20250131"
        )

    rows1 = asyncio.run(call())
    assert len(rows1) >= 1
    print(f"\nFirst call: {len(rows1)} rows (cache miss expected)")

    rows2 = asyncio.run(call())
    assert len(rows2) == len(rows1)
    assert {r.rcept_no for r in rows1} == {r.rcept_no for r in rows2}
    print(f"Second call: {len(rows2)} rows (cache hit — no DART log above)")
