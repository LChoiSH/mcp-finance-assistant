"""DART OPEN API async client.

DART (전자공시시스템) is the Korean FSS portal for corporate disclosures.
API guide: https://opendart.fss.or.kr/guide/main.do

Endpoint covered here:
    GET /api/list.json — disclosure search (공시 목록)
"""
from __future__ import annotations

import logging
import time

import httpx
from pydantic import BaseModel, Field

from config import DART_API_KEY, require

log = logging.getLogger(__name__)

DART_BASE_URL = "https://opendart.fss.or.kr/api"

STATUS_OK = "000"
STATUS_NO_DATA = "013"


class Disclosure(BaseModel):
    """One row from the DART list.json response."""

    corp_code: str
    corp_name: str
    stock_code: str | None = None
    corp_cls: str | None = None
    report_nm: str
    rcept_no: str = Field(description="Globally unique disclosure ID")
    flr_nm: str | None = None
    rcept_dt: str = Field(description="Receipt date, YYYYMMDD")
    rm: str | None = None


class DartClient:
    """Async DART client. Use as `async with DartClient() as dart: ...`."""

    def __init__(self, api_key: str | None = None, timeout: float = 10.0):
        self._api_key = require("DART_API_KEY", api_key or DART_API_KEY)
        self._client = httpx.AsyncClient(base_url=DART_BASE_URL, timeout=timeout)

    async def __aenter__(self) -> "DartClient":
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self._client.aclose()

    async def search_disclosures(
        self,
        *,
        corp_code: str | None = None,
        bgn_de: str | None = None,
        end_de: str | None = None,
        page_no: int = 1,
        page_count: int = 10,
    ) -> list[Disclosure]:
        """Search disclosures (공시 목록 조회).

        Args:
            corp_code: 8-digit DART corp code; None = all companies.
            bgn_de:    YYYYMMDD start date (inclusive).
            end_de:    YYYYMMDD end date (inclusive).
            page_no:   1-based page index.
            page_count: rows per page; DART caps at 100.

        Returns:
            List of Disclosure rows. Empty list when DART returns status 013
            ("no data") — that is a normal empty result, not an error.

        Raises:
            RuntimeError:  any other non-OK DART status code.
            httpx.HTTPError: transport-level failure.
        """
        params: dict[str, str | int] = {
            "crtfc_key": self._api_key,
            "page_no": page_no,
            "page_count": page_count,
        }
        if corp_code:
            params["corp_code"] = corp_code
        if bgn_de:
            params["bgn_de"] = bgn_de
        if end_de:
            params["end_de"] = end_de

        log.info(
            "GET /list.json corp_code=%s bgn_de=%s end_de=%s page=%d/%d",
            corp_code, bgn_de, end_de, page_no, page_count,
        )
        t0 = time.perf_counter()
        resp = await self._client.get("/list.json", params=params)
        elapsed = time.perf_counter() - t0
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status")
        rows = data.get("list", [])
        log.info(
            "← HTTP %d in %.2fs status=%s rows=%d",
            resp.status_code, elapsed, status, len(rows),
        )

        if status == STATUS_NO_DATA:
            return []
        if status != STATUS_OK:
            raise RuntimeError(
                f"DART API error: status={status} message={data.get('message')!r}"
            )
        return [Disclosure(**row) for row in rows]
