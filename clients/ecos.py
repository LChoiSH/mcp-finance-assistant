"""ECOS (한국은행 경제통계시스템) async client.

API guide: https://ecos.bok.or.kr/api/

Endpoint covered here:
    GET /StatisticSearch/{key}/json/kr/{start}/{end}/{stat_code}/{cycle}/{from}/{to}[/{item}]
"""
from __future__ import annotations

import logging
import time
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from config import ECOS_API_KEY, require

log = logging.getLogger(__name__)

ECOS_BASE_URL = "https://ecos.bok.or.kr/api"

Cycle = Literal["A", "Q", "M", "SM", "D"]


class StatRow(BaseModel):
    """One observation in an ECOS time series."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    stat_code: str = Field(alias="STAT_CODE")
    stat_name: str = Field(alias="STAT_NAME")
    item_code1: str | None = Field(default=None, alias="ITEM_CODE1")
    item_name1: str | None = Field(default=None, alias="ITEM_NAME1")
    item_code2: str | None = Field(default=None, alias="ITEM_CODE2")
    item_name2: str | None = Field(default=None, alias="ITEM_NAME2")
    item_code3: str | None = Field(default=None, alias="ITEM_CODE3")
    item_name3: str | None = Field(default=None, alias="ITEM_NAME3")
    time: str = Field(alias="TIME")
    data_value: str = Field(alias="DATA_VALUE")
    unit_name: str | None = Field(default=None, alias="UNIT_NAME")


class EcosClient:
    """Async ECOS client. Use as `async with EcosClient() as ecos: ...`."""

    def __init__(self, api_key: str | None = None, timeout: float = 10.0):
        self._api_key = require("ECOS_API_KEY", api_key or ECOS_API_KEY)
        self._client = httpx.AsyncClient(base_url=ECOS_BASE_URL, timeout=timeout)

    async def __aenter__(self) -> "EcosClient":
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self._client.aclose()

    async def search_statistics(
        self,
        *,
        stat_code: str,
        cycle: Cycle,
        start: str,
        end: str,
        item_code: str | None = None,
        max_rows: int = 1000,
    ) -> list[StatRow]:
        """Fetch a time series.

        Date format depends on cycle:
            A  = YYYY        (e.g. '2024')
            Q  = YYYYQ#      (e.g. '2024Q1')
            M  = YYYYMM      (e.g. '202401')
            SM = YYYYMM##    (semi-monthly)
            D  = YYYYMMDD    (e.g. '20240115')

        Some stat_codes require an item_code to disambiguate (e.g. exchange
        rates with multiple currencies). Most macroeconomic series do not.
        """
        parts = [
            "StatisticSearch",
            self._api_key,
            "json",
            "kr",
            "1",
            str(max_rows),
            stat_code,
            cycle,
            start,
            end,
        ]
        if item_code:
            parts.append(item_code)
        path = "/" + "/".join(parts)
        # Mask the key when logging the URL.
        log_path = path.replace(self._api_key, "***")

        log.info(
            "GET %s stat=%s cycle=%s [%s..%s]",
            log_path, stat_code, cycle, start, end,
        )
        t0 = time.perf_counter()
        resp = await self._client.get(path)
        elapsed = time.perf_counter() - t0
        resp.raise_for_status()
        data = resp.json()

        # ECOS error envelope: top-level "RESULT" key only present on errors
        # (or "no data" which is INFO-200).
        if "RESULT" in data:
            result = data["RESULT"]
            code = result.get("CODE", "")
            message = result.get("MESSAGE", "")
            if code == "INFO-200":
                log.info("← HTTP %d in %.2fs (no data)", resp.status_code, elapsed)
                return []
            raise RuntimeError(f"ECOS error: {code} {message!r}")

        rows = data.get("StatisticSearch", {}).get("row", [])
        log.info(
            "← HTTP %d in %.2fs rows=%d",
            resp.status_code, elapsed, len(rows),
        )
        return [StatRow(**row) for row in rows]
