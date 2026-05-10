"""MCP tool: get_ecos_data — Korean macroeconomic indicators from ECOS."""
from __future__ import annotations

from typing import Literal

from clients.ecos import EcosClient, StatRow


async def get_ecos_data(
    stat_code: str,
    cycle: Literal["A", "Q", "M", "SM", "D"],
    start: str,
    end: str,
    item_code: str | None = None,
) -> list[StatRow]:
    """ECOS 거시 지표 조회 — 한국은행이 제공하는 경제통계 시계열.

    사용 시점:
    - 거시 경제 지표가 필요할 때
      (기준금리, 환율, GDP, CPI, 통화량, 수출입, 산업생산 등)
    - 기간별/주기별 변화 추적 (월별/분기별/연도별)
    - 정량 거시 데이터를 다른 분석에 결합할 때
      (예: 리서치 분석 결과 + 같은 시점의 거시 환경 대조)

    사용하지 않을 때:
    - 기업 공시 자료 (사업/분기 보고서, 주요사항 등) → get_dart_disclosures 사용
    - 리서치 리포트의 사람 작성 분석/전망 → search_research_reports 사용
    - 실시간 시세 (주가, 실시간 환율): 본 도구는 ECOS 발표 데이터로 보통 일/월 단위 지연 있음

    주요 stat_code 예시:
    - 722Y001: 한국은행 기준금리 (cycle='M')
    - 731Y001: 원/달러·기타 환율 (cycle='D' 또는 'M', item_code 필요)
    - 200Y001: GDP (cycle='Q')
    - 901Y009: 소비자물가지수 CPI (cycle='M')
    - 101Y004: 경상수지 (cycle='M')

    Args:
        stat_code: ECOS 통계표 코드 (예: '722Y001').
        cycle: 'A'(연), 'Q'(분기), 'M'(월), 'SM'(반월), 'D'(일).
        start: 시작 시점. 형식은 cycle 따름:
            A=YYYY ('2024'), Q=YYYYQ# ('2024Q1'), M=YYYYMM ('202401'), D=YYYYMMDD.
        end: 종료 시점. start와 같은 형식.
        item_code: 세부 항목 코드 (선택). 환율처럼 여러 종류가 있는 통계에서 필요.

    Returns:
        시계열 행 목록. 각 행:
            - stat_code, stat_name: 통계표 식별
            - time: 관측 시점 (cycle 형식)
            - data_value: 값 (문자열 — 단위는 unit_name 참조)
            - unit_name: 단위 (예: '%', '원')
            - item_code1/name1, item_code2/name2: 세부 항목 분류 (있을 때)
    """
    async with EcosClient() as ecos:
        return await ecos.search_statistics(
            stat_code=stat_code,
            cycle=cycle,
            start=start,
            end=end,
            item_code=item_code,
        )
