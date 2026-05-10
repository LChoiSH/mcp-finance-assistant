# PLAN

이 프로젝트는 **면접 설명용**입니다. 데모 시연 없음.

`Decisions.md` 우선순위를 그대로 따릅니다:
1. 코드 동작 (본인 검증용)
2. **Decisions.md** ← 진짜 산출물
3. 아키텍처 다이어그램
4. README 간결하게

---

## 현재 상태 (2026-05-10)

### 코드 — 완료
- [x] uv 환경 + 의존성
- [x] MCP 서버 스캐폴드 (FastMCP, stdio)
- [x] DART 클라이언트 + cache-aside repository (incremental day coverage)
- [x] `get_dart_disclosures` MCP tool — 라이브 검증 ✅
- [x] RAG 인프라 (LlamaIndex + Chroma + bge-m3 lazy load)
- [x] `search_research_reports` MCP tool — 코드 완료, PDF 대기
- [x] ECOS 클라이언트 + `get_ecos_data` tool — 라이브 검증 ✅
- [x] 3-way tool description cross-reference 자동 검증 테스트
- [x] Production 로깅 (DART/repository) + httpx URL 키 마스킹

### 산출물 — 작업 중
- [ ] Decisions.md 디테일 보완 (구현하며 발견한 것 반영)
- [ ] architecture.md (Mermaid 다이어그램)
- [ ] README 본문 확장 (현재는 setup/run/debug만)
- [ ] 면접 토킹포인트 5개 (Decisions.md에서 추출)

### 옵션 (필수 아님)
- [ ] PDF 25개 인덱싱 → search_research_reports 라이브 검증
- [ ] Claude Code `.mcp.json` 등록 → 자연어 질의 직접 호출
- [ ] Tool description 미세 조정 (이미 cross-reference 자동 검증 있음)

---

## 우선순위 — 남은 작업

데모 안 하니까 **"내가 면접에서 설명할 때 필요한 것"** 기준으로 정렬:

1. **Decisions.md 보완** — 면접 답변의 단일 출처. 구현 중 발견한 디테일 (예: bge-m3 전환, lazy import, key masking) 반영
2. **architecture.md** — 3-layer 데이터 아키텍처 시각화. 면접에서 "이거 그려가며 설명할게요" 가능하게
3. **README 본문** — 면접 전 5분 브리핑용. 시스템 개요 + 실행법 + Decisions/architecture로 링크
4. **토킹포인트 5개** — 묻지 않아도 자연스럽게 꺼낼 5가지

코드 라이브 검증 (PDF 인덱싱)은 본인 자신감용이지 산출물 아님. 시간 남으면.

---

## 면접 답변 골격 (토킹포인트 채우기 전 메모)

대화 흐름 시뮬레이션:

> Q: "이 프로젝트 5분 정도로 설명해주세요"
> 
> A:
> 1. **무엇** — 한국 금융 도메인 MCP 서버. 3개 도구 (RAG / DART / ECOS) 노출
> 2. **왜 MCP** — 공고 매칭 + LLM-도구 분리 표준
> 3. **3 데이터 레이어 설계** — 변동성 × 접근 패턴 × 저장 전략 차등
> 4. **Cache-aside 차등 적용** — DART는 캐싱, ECOS는 직접. *naive hit/miss 아닌 incremental day coverage*
> 5. **Tool description = LLM 라우팅 프롬프트** — cross-reference로 정확도 확보, 자동 검증 테스트까지 박음

각 항목 30초~1분, 합쳐서 5분. 이게 토킹포인트 5개의 초안.

---

## 면접 토킹포인트 5개 (산출물 작업 끝낸 후 확정)

1. _________________ (MCP 채택 — 공고 매칭 + 표준화 가치)
2. _________________ (3 데이터 레이어 — 변동성별 차등 정책)
3. _________________ (cache-aside incremental — 단순 hit/miss 아님)
4. _________________ (tool description as routing prompt — cross-reference + 자동 검증)
5. _________________ (의도적 제외 — provider 추상화, HTTP transport, 데모 등)

---

## 폴더 구조 (현재)

```
mirae-project/
├── pyproject.toml, uv.lock, .python-version
├── .env (gitignored), .env.example, .gitignore
├── README.md, Decisions.md, Plan.md, CLAUDE.md
├── architecture.md          # 작업 예정
├── server.py                # MCP 진입점, 3 tool 등록
├── config.py                # .env + 경로 + 로거 silence
├── tools/{disclosures, research, macro}.py
├── clients/{dart, ecos}.py
├── rag/{embedding, indexer, retriever}.py
├── storage/{db, models, repository}.py
├── scripts/index_pdfs.py
├── data/{pdfs/, chroma/, cache.db} (gitignored)
└── tests/                   # 13 passed, 1 skipped
```

---

## 리스크 (남은 것만)

| 리스크 | 대응 |
|---|---|
| Decisions.md가 코드와 어긋남 | 산출물 작업 시 코드 1회 read-through |
| 토킹포인트가 진부함 | "안 한 것" (Decisions.md 마지막 표) 를 적극 활용 — 면접관에게 *"의도적 trade-off를 인지한 사람"* 시그널 |
| 면접에서 시연 요구 | 코드 + Inspector 로그 스크린샷 1~2장 준비. 라이브 시연은 환경 변수에 좌우되니 회피 |
