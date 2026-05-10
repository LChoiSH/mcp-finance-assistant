"""DART disclosure repository — cache-aside with incremental day coverage.

Per Decisions.md §7:
    - Past dates: cache forever (immutable).
    - Today: never marked as covered (still mutating intra-day), so callers
      always re-fetch today's slice.
"""
from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

from clients.dart import Disclosure
from storage.db import connect
from storage.models import MissingRange

log = logging.getLogger(__name__)


def _parse(yyyymmdd: str) -> date:
    return date(int(yyyymmdd[0:4]), int(yyyymmdd[4:6]), int(yyyymmdd[6:8]))


def _format(d: date) -> str:
    return d.strftime("%Y%m%d")


def _days_in(bgn_de: str, end_de: str) -> list[str]:
    start, end = _parse(bgn_de), _parse(end_de)
    if start > end:
        return []
    out: list[str] = []
    cur = start
    while cur <= end:
        out.append(_format(cur))
        cur += timedelta(days=1)
    return out


def _group_consecutive(days: list[str]) -> list[MissingRange]:
    if not days:
        return []
    days = sorted(days)
    ranges: list[MissingRange] = []
    start = prev = days[0]
    for d in days[1:]:
        if _parse(d) - _parse(prev) == timedelta(days=1):
            prev = d
            continue
        ranges.append(MissingRange(bgn_de=start, end_de=prev))
        start = prev = d
    ranges.append(MissingRange(bgn_de=start, end_de=prev))
    return ranges


class DartRepository:
    """Cache-aside repository for DART disclosures."""

    def __init__(self, db_path: Path | None = None):
        self._conn = connect(db_path)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "DartRepository":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def find_disclosures(
        self,
        *,
        corp_code: str,
        bgn_de: str,
        end_de: str,
    ) -> list[Disclosure]:
        cur = self._conn.execute(
            """
            SELECT corp_code, corp_name, stock_code, corp_cls,
                   report_nm, rcept_no, flr_nm, rcept_dt, rm
              FROM disclosures
             WHERE corp_code = ?
               AND rcept_dt BETWEEN ? AND ?
             ORDER BY rcept_dt DESC, rcept_no DESC
            """,
            (corp_code, bgn_de, end_de),
        )
        out = [Disclosure(**dict(r)) for r in cur.fetchall()]
        log.info(
            "find corp=%s [%s..%s] → %d rows", corp_code, bgn_de, end_de, len(out)
        )
        return out

    def missing_ranges(
        self,
        *,
        corp_code: str,
        bgn_de: str,
        end_de: str,
        today: str,
    ) -> list[MissingRange]:
        """Return contiguous date ranges NOT yet covered for this corp."""
        all_days = _days_in(bgn_de, end_de)
        if not all_days:
            return []
        cur = self._conn.execute(
            """
            SELECT rcept_dt FROM fetched_days
             WHERE corp_code = ? AND rcept_dt BETWEEN ? AND ?
            """,
            (corp_code, bgn_de, end_de),
        )
        covered = {r["rcept_dt"] for r in cur.fetchall()}
        covered.discard(today)
        missing = [d for d in all_days if d not in covered]
        ranges = _group_consecutive(missing)
        log.info(
            "missing_ranges corp=%s [%s..%s] → %d ranges (%d/%d days uncovered)",
            corp_code, bgn_de, end_de, len(ranges), len(missing), len(all_days),
        )
        return ranges

    def save_disclosures(
        self,
        *,
        corp_code: str,
        bgn_de: str,
        end_de: str,
        disclosures: Iterable[Disclosure],
        today: str,
    ) -> int:
        """Upsert rows; mark days in [bgn_de, end_de] as fetched (today excluded).

        Returns the number of rows upserted.
        """
        now = int(time.time())
        rows = list(disclosures)
        with self._conn:
            self._conn.executemany(
                """
                INSERT INTO disclosures
                    (rcept_no, corp_code, corp_name, stock_code, corp_cls,
                     report_nm, flr_nm, rcept_dt, rm, cached_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(rcept_no) DO UPDATE SET
                    corp_name=excluded.corp_name,
                    stock_code=excluded.stock_code,
                    corp_cls=excluded.corp_cls,
                    report_nm=excluded.report_nm,
                    flr_nm=excluded.flr_nm,
                    rcept_dt=excluded.rcept_dt,
                    rm=excluded.rm,
                    cached_at=excluded.cached_at
                """,
                [
                    (
                        d.rcept_no, d.corp_code, d.corp_name, d.stock_code,
                        d.corp_cls, d.report_nm, d.flr_nm, d.rcept_dt, d.rm, now,
                    )
                    for d in rows
                ],
            )
            days_to_mark = [d for d in _days_in(bgn_de, end_de) if d != today]
            self._conn.executemany(
                """
                INSERT OR REPLACE INTO fetched_days (corp_code, rcept_dt, cached_at)
                VALUES (?, ?, ?)
                """,
                [(corp_code, d, now) for d in days_to_mark],
            )
        log.info(
            "save corp=%s [%s..%s] rows=%d days_marked=%d",
            corp_code, bgn_de, end_de, len(rows), len(days_to_mark),
        )
        return len(rows)
