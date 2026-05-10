"""MCP tool: search_research_reports — semantic search over indexed PDFs."""
from __future__ import annotations

import asyncio
from typing import Any

from rag.retriever import retrieve


async def search_research_reports(
    query: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """리서치 리포트 검색 — 한국 증권사/연구기관 PDF에서 의미 기반 검색.

    사용 시점:
    - 사람이 작성한 분석/전망/투자의견이 필요할 때
      (예: '반도체 업황 전망', '부동산 PF 리스크 분석', '2차전지 수요 시나리오')
    - 정성적 설명, 시장 해석, 산업 동향이 필요할 때
    - 특정 산업/섹터에 대한 종합 시각이 필요할 때

    사용하지 않을 때:
    - 공식 공시 자료 (사업보고서, 주요사항보고서, 자기주식 등) → get_dart_disclosures 사용
    - 거시 경제 지표 (금리, 환율, GDP, CPI 등) → get_ecos_data 사용
    - 실시간 주가/시총: 본 도구 범위 밖 (외부 시세 API 별도 필요)

    Args:
        query: 자연어 검색어 (예: '반도체 메모리 업황', '금리 인상 영향').
        top_k: 반환할 청크 개수. 기본 5.

    Returns:
        유사도 점수 순으로 정렬된 청크 목록. 각 항목:
            - score: 유사도 점수 (높을수록 관련성 높음)
            - text:  청크 본문
            - metadata: 출처 PDF 정보 (file_name 등)
    """
    return await asyncio.to_thread(retrieve, query=query, top_k=top_k)
