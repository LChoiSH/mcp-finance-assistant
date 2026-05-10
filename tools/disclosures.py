"""MCP tool: get_dart_disclosures.

Wires DartRepository (cache) and DartClient (live API) together.
Per Decisions.md §7, only missing day-ranges trigger DART calls.
"""
from __future__ import annotations

from datetime import date

from clients.dart import DartClient, Disclosure
from storage.repository import DartRepository


async def get_dart_disclosures(
    corp_code: str,
    bgn_de: str,
    end_de: str,
) -> list[Disclosure]:
    """DART 공시(disclosure) 조회 — 한국 상장기업의 공식 공시 자료.

    사용 시점:
    - 특정 기업의 공시 이력이 필요할 때 (사업/분기보고서, 주요사항보고서, 자기주식 등)
    - 기간 내 공시 변동 추적 (인사 변동, 자본구조, 합병/분할, 대량보유 등)
    - DART에 등록된 정형 공시 데이터를 직접 사용하고 싶을 때

    사용하지 않을 때:
    - 리서치 리포트의 분석/전망/투자의견이 필요한 경우 → search_research_reports 사용
    - 거시 지표(금리, 환율, GDP, CPI 등)가 필요한 경우 → get_ecos_data 사용
    - 회사 corp_code를 모를 때 → 본 도구는 corp_code를 입력으로 받음. 이름→코드 변환은 별도 단계 필요.

    Args:
        corp_code: DART 8자리 고유번호 (예: 삼성전자=00126380, SK하이닉스=00164779).
        bgn_de: 조회 시작일 YYYYMMDD (예: '20250101').
        end_de: 조회 종료일 YYYYMMDD (예: '20250331').

    Returns:
        공시 목록. 각 항목은 corp_name, report_nm(보고서명), rcept_dt(접수일),
        rcept_no(접수번호), stock_code 등을 포함.
    """
    today = date.today().strftime("%Y%m%d")

    with DartRepository() as repo:
        missing = repo.missing_ranges(
            corp_code=corp_code, bgn_de=bgn_de, end_de=end_de, today=today
        )
        if missing:
            async with DartClient() as dart:
                for r in missing:
                    rows = await dart.search_disclosures(
                        corp_code=corp_code,
                        bgn_de=r.bgn_de,
                        end_de=r.end_de,
                        page_count=100,
                    )
                    repo.save_disclosures(
                        corp_code=corp_code,
                        bgn_de=r.bgn_de,
                        end_de=r.end_de,
                        disclosures=rows,
                        today=today,
                    )

        return repo.find_disclosures(
            corp_code=corp_code, bgn_de=bgn_de, end_de=end_de
        )
