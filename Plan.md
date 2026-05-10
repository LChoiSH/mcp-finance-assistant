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

### 알려진 한계 (Deferred)

| 한계 | 영향 | 대응 (deferred) |
|---|---|---|
| uvx-from-git 모드: 캐시 비영속 | 매 세션마다 DART API 재호출 (캐시 hit 0) | `config.py`에서 `CACHE_DB`/`CHROMA_DIR`을 `~/.cache/finance-mcp-assistant/`로 이전 (~30분) |
| uvx-from-git 모드: RAG 사용 불가 | search_research_reports가 사실상 로컬 clone 모드 전용 | PDF 경로 외부화 + 인덱스 경로 외부화. 위 캐시 작업과 같이 처리 권장 |

**원인**: Decisions.md §14 한계 참조. *"uvx는 매 실행 시 임시 디렉토리에 격리 설치"* 가 본질.

**의사결정**: 면접 산출물 우선이라 distribution 마지막 1마일은 deferred. 현재는 *시나리오 B (로컬 clone)* 가 풀 기능.

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

## 면접 토킹포인트 5개 (확정)

각 항목은 *묻지 않아도 자연스럽게 꺼낼* 수 있도록. 30초~1분 길이.

### 1. MCP 채택 — "새 발명이 아니라 컨벤션화"

> "MCP는 LLM-도구 통합 패턴의 컨벤션화입니다. REST API + Function Calling으로도 동일 동작 구현 가능하지만, MCP가 표준화한 건 *도구 정의 스키마 / 호출 메시지 형식 / 도구 발견 절차 / 에러 처리* 네 가지입니다. HTTP가 TCP 위에 메시지 형식을 표준화했듯, MCP는 LLM-도구 통합의 컨벤션을 통일했고, 이게 회사 환경(N개 클라이언트 × M개 도구) 에서 가치가 발현되는 지점입니다."

- 참조: Decisions.md §1
- 코드: `server.py` (FastMCP 데코레이터로 한 줄 등록)
- 면접관 fallback 질문 대비: *"REST API와 차이?"* → "self-describing, runtime 사용, 메시지 형식 표준화"

### 2. 3 데이터 레이어 — "모든 데이터를 동일하게 다루지 않는다"

> "이 시스템은 데이터의 변동성과 접근 패턴에 따라 세 가지 저장 전략을 가집니다. 리서치 PDF는 *불변 + 의미검색* 이라 사전 임베딩 후 Chroma. DART 공시는 *과거는 불변, 오늘은 mutating* 이라 cache-aside SQLite. ECOS 거시 지표는 *월/분기 갱신 + 호출 빈도 낮음* 이라 캐싱 ROI가 안 나와서 직접 호출. 모든 데이터를 똑같이 캐싱하거나, 똑같이 직접 호출하는 게 흔한 실수라고 봤습니다."

- 참조: Decisions.md §7, §8 / architecture.md §2
- 코드: `tools/{research,disclosures,macro}.py` 각각이 다른 백엔드

### 3. Cache-aside는 incremental — "단순 hit/miss가 아니라 차분"

> "DART 캐시는 단순 키-매칭 hit/miss가 아니라 per-day coverage로 추적합니다. 사용자가 [Jan 1, Mar 31] 요청하고 [Jan 1, Feb 15]만 캐시에 있다면 missing_ranges가 [Feb 16, Mar 31]만 반환해서 그 차분만큼만 DART API를 호출합니다. 두 테이블 분리(`disclosures` + `fetched_days`)가 핵심 — *0건짜리 날도 조회됨*으로 마킹해야 다음에 재호출이 안 되니까요. 그리고 오늘 날짜는 영구 마킹 대상에서 제외 — 장중에 추가되는 공시를 놓치지 않으려고."

- 참조: Decisions.md §7 / architecture.md §3 (sequence diagram)
- 코드: `storage/repository.py::missing_ranges`, `save_disclosures`
- 검증: `tests/test_dart_repository.py::test_today_excluded_from_coverage` + `test_repo_with_live_dart`

### 4. Tool description = LLM 라우팅 프롬프트 — "회귀 방지까지"

> "Tool description은 단순 docstring이 아니라 LLM이 도구를 *언제 부를지/안 부를지* 결정하는 프롬프트입니다. 그래서 *사용 시점 / 사용하지 않을 때 → 형제 tool 명시* 형식을 강제했고, 도구 3개가 서로를 cross-reference 합니다. 가장 중요한 건 이 cross-reference가 자동 회귀 테스트로 묶여있다는 점입니다 — 누가 description 다듬다가 형제 tool 이름을 실수로 빼면 테스트가 깨집니다. *Tool description의 프롬프트 엔지니어링은 코드처럼 회귀 가능한 자산*이라는 게 제 결론이었습니다."

- 참조: Decisions.md §9
- 코드: `tools/{disclosures,research,macro}.py`의 docstring
- 검증: `tests/test_tool_macro.py::test_descriptions_cross_reference_each_other`

### 5. 의도적 제외 — "안 한 것이 곧 trade-off"

> "Decisions.md에 *안 한 것* 표를 명시적으로 둔 이유는, 안 한 것을 모르는 채 안 한 것과 알면서 안 한 것이 다르기 때문입니다. 대표 예: LLM provider 추상화 — MCP가 이미 그 추상화고 위에 또 올리면 군더더기. HTTP transport — 사이드 프로젝트엔 stdio가 적합하고 FastMCP가 한 줄로 전환 가능. PyPI publish — 유지보수 의무 부담이 사이드 프로젝트엔 과해서 uvx-from-git이 적정점. 한경컨센서스 스크래퍼 — ToS 회색지대라 합법 대체(KCMI/KIF/KIET)를 권장. *알면서 멈춘 trade-off*는 지표라 생각합니다."

- 참조: Decisions.md "안 한 것" 표 + §14 (distribution) + §13 (lazy import) + 한계 섹션들
- 토킹포인트로 좋은 이유: 면접관이 "왜 X 안 했나?" 물을 때 짧게 답할 수 있음

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
