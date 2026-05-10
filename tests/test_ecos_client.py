"""Live ECOS API test — single call to a stable indicator.

Skips when ECOS_API_KEY is not configured.
"""
from __future__ import annotations

import asyncio

import pytest

from clients.ecos import EcosClient
from config import ECOS_API_KEY

BASE_RATE_STAT_CODE = "722Y001"  # 한국은행 기준금리


@pytest.mark.skipif(not ECOS_API_KEY, reason="ECOS_API_KEY not set")
def test_search_base_rate_2024_monthly():
    """기준금리 2024년 월별 — should return >= 1 observation."""

    async def run():
        async with EcosClient() as ecos:
            return await ecos.search_statistics(
                stat_code=BASE_RATE_STAT_CODE,
                cycle="M",
                start="202401",
                end="202412",
            )

    rows = asyncio.run(run())
    assert len(rows) >= 1, "Expected at least one base-rate observation"

    print(f"\nGot {len(rows)} rows. Sample:")
    for r in rows[:3]:
        unit = f" {r.unit_name}" if r.unit_name else ""
        print(f"  {r.time}: {r.data_value}{unit} ({r.stat_name})")
