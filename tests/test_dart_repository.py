"""DART repository — cache-aside + incremental coverage tests.

`test_repo_lifecycle` runs offline with synthetic rows.
`test_repo_with_live_dart` performs one real DART call to exercise the full path.
"""
from __future__ import annotations

import asyncio

import pytest

from clients.dart import Disclosure, DartClient
from config import DART_API_KEY
from storage.repository import DartRepository

SAMSUNG_CORP_CODE = "00126380"


def test_repo_lifecycle(tmp_path):
    db = tmp_path / "test.db"
    today = "20260509"

    with DartRepository(db_path=db) as repo:
        # Empty cache — full range is missing
        missing = repo.missing_ranges(
            corp_code="00126380", bgn_de="20250101", end_de="20250105", today=today
        )
        assert len(missing) == 1
        assert (missing[0].bgn_de, missing[0].end_de) == ("20250101", "20250105")

        # Save one row covering the range
        sample = [
            Disclosure(
                corp_code="00126380",
                corp_name="삼성전자",
                stock_code="005930",
                report_nm="테스트보고서",
                rcept_no="20250103000001",
                rcept_dt="20250103",
            )
        ]
        n = repo.save_disclosures(
            corp_code="00126380",
            bgn_de="20250101",
            end_de="20250105",
            disclosures=sample,
            today=today,
        )
        assert n == 1

        # Full hit
        assert repo.missing_ranges(
            corp_code="00126380", bgn_de="20250101", end_de="20250105", today=today
        ) == []

        # Partial overlap — only the un-fetched suffix should remain
        partial = repo.missing_ranges(
            corp_code="00126380", bgn_de="20250103", end_de="20250108", today=today
        )
        assert len(partial) == 1
        assert (partial[0].bgn_de, partial[0].end_de) == ("20250106", "20250108")

        # Find returns the saved row
        rows = repo.find_disclosures(
            corp_code="00126380", bgn_de="20250101", end_de="20250105"
        )
        assert len(rows) == 1
        assert rows[0].rcept_no == "20250103000001"

        # Idempotent re-save
        n = repo.save_disclosures(
            corp_code="00126380",
            bgn_de="20250101",
            end_de="20250105",
            disclosures=sample,
            today=today,
        )
        assert n == 1
        rows = repo.find_disclosures(
            corp_code="00126380", bgn_de="20250101", end_de="20250105"
        )
        assert len(rows) == 1, "upsert should not duplicate by rcept_no"


def test_today_excluded_from_coverage(tmp_path):
    db = tmp_path / "today.db"
    today = "20250105"

    with DartRepository(db_path=db) as repo:
        repo.save_disclosures(
            corp_code="00126380",
            bgn_de="20250101",
            end_de="20250105",
            disclosures=[],
            today=today,
        )
        # 20250101..20250104 should be covered, 20250105 (today) should not
        missing = repo.missing_ranges(
            corp_code="00126380", bgn_de="20250101", end_de="20250105", today=today
        )
        assert len(missing) == 1
        assert (missing[0].bgn_de, missing[0].end_de) == ("20250105", "20250105")


@pytest.mark.skipif(not DART_API_KEY, reason="DART_API_KEY not set")
def test_repo_with_live_dart(tmp_path):
    """End-to-end: cache miss → DART → save → cache hit."""
    db = tmp_path / "live.db"
    today = "20260509"
    bgn, end = "20250101", "20250131"

    async def fetch():
        async with DartClient() as dart:
            return await dart.search_disclosures(
                corp_code=SAMSUNG_CORP_CODE,
                bgn_de=bgn,
                end_de=end,
                page_count=100,
            )

    with DartRepository(db_path=db) as repo:
        missing = repo.missing_ranges(
            corp_code=SAMSUNG_CORP_CODE, bgn_de=bgn, end_de=end, today=today
        )
        assert len(missing) == 1, "fresh DB should report full range as missing"

        rows = asyncio.run(fetch())
        print(f"\nDART returned {len(rows)} rows for Samsung Jan 2025")

        repo.save_disclosures(
            corp_code=SAMSUNG_CORP_CODE,
            bgn_de=bgn,
            end_de=end,
            disclosures=rows,
            today=today,
        )

        assert repo.missing_ranges(
            corp_code=SAMSUNG_CORP_CODE, bgn_de=bgn, end_de=end, today=today
        ) == [], "after save the range should be fully covered"

        cached = repo.find_disclosures(
            corp_code=SAMSUNG_CORP_CODE, bgn_de=bgn, end_de=end
        )
        assert len(cached) == len(rows)
        print(f"Cache stored and recovered {len(cached)} rows.")
