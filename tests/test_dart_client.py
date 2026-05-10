"""Live DART API test — hits the real endpoint once.

Skips silently when DART_API_KEY is not configured, so the test suite
stays green in environments without secrets.
"""
from __future__ import annotations

import asyncio

import pytest

from clients.dart import DartClient
from config import DART_API_KEY

SAMSUNG_CORP_CODE = "00126380"


@pytest.mark.skipif(not DART_API_KEY, reason="DART_API_KEY not set")
def test_search_disclosures_samsung_q1_2025():
    """Samsung Q1 2025 disclosures — quarterly reports period, expects rows."""

    async def run():
        async with DartClient() as dart:
            return await dart.search_disclosures(
                corp_code=SAMSUNG_CORP_CODE,
                bgn_de="20250101",
                end_de="20250331",
                page_count=5,
            )

    rows = asyncio.run(run())

    assert len(rows) >= 1, "Expected at least one Samsung disclosure in Q1 2025"

    print(f"\nGot {len(rows)} disclosures. Sample:")
    for r in rows[:3]:
        print(f"  [{r.rcept_dt}] {r.corp_name} — {r.report_nm} (rcept_no={r.rcept_no})")
