# 포트폴리오 자료 — finance-mcp-assistant

이 문서는 포트폴리오/이력서/면접 답변에 그대로 또는 발췌해서 사용 가능한 콘텐츠 모음입니다. 길이별/용도별로 정리했으니 매체에 맞게 골라 쓰세요.

---

## 1. 1줄 요약 (이력서 한 줄용)

선택지 — 가장 잘 맞는 걸로:

- **공고 키워드 매칭형**:
  > "MCP 기반 한국 금융 도메인 LLM 도구 서버 — Claude/GPT가 DART 공시·ECOS 거시·리서치 PDF에 접근하도록 단일 프로토콜로 통합"

- **기술 임팩트형**:
  > "MCP 서버 + Hybrid RAG (vector + 정형 캐시 + 실시간 API) — 3 데이터 레이어를 LLM 라우팅으로 통합한 한국 금융 어시스턴트"

- **간결형**:
  > "Python MCP 서버로 한국 금융 데이터 3종(DART 공시, ECOS 거시, 리서치 PDF)을 LLM에 연결"

---

## 2. 한 문단 (포트폴리오 카드)

> Claude/GPT 같은 LLM이 한국 금융 데이터에 표준 인터페이스로 접근할 수 있도록 만든 **MCP (Model Context Protocol) 서버**입니다. 단일 서버에서 세 가지 도구를 노출 — 리서치 리포트 PDF의 의미 검색(bge-m3 + Chroma), DART 공시 조회(SQLite cache-aside), ECOS 거시 지표(직접 호출). 핵심 설계는 **데이터 변동성과 접근 패턴에 따라 저장 전략을 차등 적용**한 점이고, 캐시는 단순 hit/miss가 아니라 *부분 캐시 + 차분 페치*로 설계했습니다. Tool description을 LLM 라우팅 프롬프트로 취급해 cross-reference 자동 회귀 테스트까지 두었고, 전체 시스템을 `uvx --from git+...` 한 줄로 배포 가능한 형태로 패키징했습니다. Python 3.11, FastMCP, LlamaIndex, Chroma, SQLite, httpx, Pydantic, uv/hatchling 사용. **단일 SSOT 문서(Decisions.md)에 모든 설계 결정을 *선택/이유/대안/한계/면접 답변* 5단으로 기록**했습니다.

---

## 3. 상세 프로젝트 페이지 (Notion / 개인 사이트용)

### 배경 / 동기

채용 공고가 명시한 키워드 — *MCP 기반 커넥터 개발 / AI 에이전트 / RAG 파이프라인 / PB·리서치 업무 지원 LLM Assistant / 사내 데이터-LLM 연동 백엔드 API / 금융 도메인* — 모두를 한 시스템으로 매칭하는 것이 목표였습니다. MCP는 2024~2025 표준화 흐름의 핵심이라 "이미 있는 것을 채택했다"가 아니라 **설계 의도를 가지고 채택한 것**으로 답변할 수 있어야 했습니다.

### 역할 / 기간

- **단독 설계 + 구현**
- 약 2일 집중 개발 (코드 + 산출물 4종)
- AI 페어 프로그래밍 활용 (Claude Code), 결정/근거는 본인 책임

### 기술 스택

| 영역 | 선택 | 이유 (요약) |
|---|---|---|
| MCP SDK | `mcp` Python (FastMCP, stdio) | 공식 SDK, 데코레이터 기반 고수준 API |
| Async HTTP | `httpx` | MCP SDK가 async 기반, DART/ECOS 비동기 호출 |
| 데이터 검증 | `pydantic` | LLM/외부 API 응답 런타임 검증, MCP SDK 내부 사용 |
| RAG 파이프라인 | `llama-index` + `chromadb` | 검증된 패턴, 청킹/임베딩/검색 자동화 |
| 임베딩 | `BAAI/bge-m3` (로컬, MPS 가속) | 외부 API 의존성 0, 한국어 우수, 자족적 데모 가능 |
| 캐시 | SQLite (stdlib) | 단일 파일, 사이드 프로젝트 규모 충분 |
| 패키징 | `uv` + `hatchling` | pip 대비 10~100배, lock 재현성, 빠른 빌드 |
| 배포 | `uvx --from git+...` | PyPI 유지보수 의무 회피, clone 불필요한 sweet spot |

### 시스템 아키텍처

**3 데이터 레이어 — 변동성 × 접근 패턴 × 저장 전략 차등**:

| Layer | 데이터 | 변동성 | 호출 빈도 | 저장 전략 |
|---|---|---|---|---|
| 1 | 리서치 리포트 PDF | 불변 | (인덱싱 1회) | 사전 임베딩 → Chroma vector |
| 2 | DART 공시 | 과거 불변 / 오늘 변경 | 자주 | SQLite cache-aside (incremental) |
| 3 | ECOS 거시 지표 | 월/분기 갱신 | 적음 | 직접 호출 (캐시 ROI 낮음) |

각 레이어는 별도 MCP 도구로 노출 — `search_research_reports`, `get_dart_disclosures`, `get_ecos_data`. 도구 자체는 독립이지만 **클라이언트 LLM이 자연어 질의를 받아 자동 라우팅**합니다.

상세 다이어그램 6종: [architecture.md](architecture.md)

### 핵심 설계 결정 (5가지)

1. **MCP 채택의 본질** — 새 발명이 아니라 *LLM-도구 통합 패턴의 컨벤션화*. REST + Function Calling으로 동일 동작 가능하지만 MCP는 도구 정의 스키마 / 호출 메시지 형식 / 도구 발견 절차 / 에러 처리를 표준화. *"HTTP가 TCP 위에 메시지 형식 표준화한 것과 같다"*.

2. **Cache-aside는 incremental이지 hit/miss 아님** — `disclosures` 테이블 외에 `fetched_days` 테이블을 분리해 *날짜 단위로 조회 여부*를 추적. 사용자가 [Jan 1, Mar 31] 요청하고 [Jan 1, Feb 15]만 캐시에 있으면 **차분 [Feb 16, Mar 31]만 DART에 호출**. 0건짜리 날도 *조회됨*으로 마킹해야 다음에 재호출 안 됨. 오늘 날짜는 영구 마킹 제외 (장중 추가 공시 가능성).

3. **Tool description = LLM 라우팅 프롬프트** — 단순 docstring 아니라 LLM이 *언제 부를지/안 부를지* 결정하는 프롬프트. *"사용 시점 / 사용하지 않을 때 → 형제 tool 명시"* 형식 강제. 3개 도구가 서로 cross-reference하고, **이 cross-reference가 자동 회귀 테스트로 묶여있음** (description에서 형제 tool 이름이 빠지면 테스트 깨짐).

4. **Lazy import discipline** — torch + sentence-transformers는 함수 본문 안에서 import. **stdio MCP 서버는 매 클라이언트 spawn마다 fresh 프로세스**라 startup이 UX 직격타. 측정값: 모듈 import **35s → 2.87s** (12배). DART/ECOS 도구만 쓰는 사용자는 ML 의존성 끝까지 안 끌어들임.

5. **의도적 제외 (Trade-off로 명시)** — LLM provider 추상화(MCP가 그 역할), HTTP transport(사이드 프로젝트엔 stdio 적합), PyPI publish(유지보수 의무), 데모 시연 자동화(면접 환경 시연 안 함), 자체 임베딩 추상화(LlamaIndex BaseEmbedding이 표준) 등을 **각각 이유 명시해서 거부**. 알면서 안 한 것이 무엇인지가 알면서 한 것보다 중요.

### 차별화 포인트

- **Hybrid RAG** — 단일 vector store가 아니라 vector + structured + live API를 LLM 라우팅으로 통합. *"단순 RAG가 아닌 진화형"* 으로 표현 가능.
- **자동 회귀 가능한 프롬프트 엔지니어링** — Tool description의 cross-reference를 unit test로 검증. *프롬프트도 코드처럼 회귀 가능한 자산* 이라는 결론.
- **운영 관점 디테일** — API 키가 URL에 포함되는 ECOS의 특성을 발견해 logger silence + 자체 로그 마스킹으로 *로깅도 보안 경계* 적용.
- **SSOT 문서화** — Decisions.md 한 파일에 모든 설계 결정을 *선택/이유/대안/한계/면접 답변* 5단으로 정리. 코드와 문서의 정합성을 고의적으로 강제.
- **Distribution 마지막 1마일 인지** — `uvx --from git+...` 한 줄 실행되게 패키징. 단 *uvx 모드 캐시 비영속* 한계는 deferred로 명시 — 알면서 멈춘 trade-off.

### 결과

- **코드**: 14 pytest 통과 (DART 라이브 / ECOS 라이브 / RAG 스모크 / 3-way cross-reference 자동 검증)
- **성능**: 모듈 import 35s → 2.87s (lazy import 적용), DART API 호출 평균 0.3~0.5s
- **배포**: GitHub public, `uvx --from git+...` 한 줄 실행 가능, 휠 빌드 정상
- **문서**: 5종 산출물 (Decisions / Plan / README / architecture / CLAUDE), 모두 정합성 유지

### 회고 / 한계

- **PDF 표 데이터 추출 약함** — LlamaIndex 기본 로더 한계. 프로덕션이면 표 추출 별도 파서 + 구조화 데이터 저장 하이브리드 고려.
- **uvx 모드 캐시 임시 디렉토리** — `~/.cache/`로 옮기면 ~30분에 해결되지만 면접 산출물 우선이라 deferred.
- **회사명 → corp_code 변환 도구 부재** — 사용자가 코드 알아야 함. 별도 lookup tool 추가 가능하지만 현재 범위에서 제외.
- **답변 품질 평가(RAGAS 등) 없음** — 프로덕션 영역, 사이드 프로젝트 범위 초과로 의도적 제외.

---

## 4. 면접 답변 5개 (확정본)

각 30초~1분 길이. Plan.md에서 발췌.

### 1. MCP 채택 — "새 발명이 아니라 컨벤션화"
> "MCP는 LLM-도구 통합 패턴의 컨벤션화입니다. REST API + Function Calling으로도 동일 동작 구현 가능하지만, MCP가 표준화한 건 *도구 정의 스키마 / 호출 메시지 형식 / 도구 발견 절차 / 에러 처리* 네 가지입니다. HTTP가 TCP 위에 메시지 형식을 표준화했듯, MCP는 LLM-도구 통합의 컨벤션을 통일했고, 회사 환경(N개 클라이언트 × M개 도구) 에서 가치가 발현되는 지점입니다."

### 2. 3 데이터 레이어 — "모든 데이터를 동일하게 다루지 않는다"
> "이 시스템은 데이터의 변동성과 접근 패턴에 따라 세 가지 저장 전략을 가집니다. 리서치 PDF는 *불변 + 의미검색* 이라 사전 임베딩 후 Chroma. DART 공시는 *과거는 불변, 오늘은 mutating* 이라 cache-aside SQLite. ECOS 거시 지표는 *월/분기 갱신 + 호출 빈도 낮음* 이라 캐싱 ROI가 안 나와서 직접 호출. 모든 데이터를 똑같이 캐싱하거나 똑같이 직접 호출하는 게 흔한 실수라고 봤습니다."

### 3. Cache-aside는 incremental — "단순 hit/miss가 아니라 차분"
> "DART 캐시는 단순 키-매칭 hit/miss가 아니라 per-day coverage로 추적합니다. 사용자가 [Jan 1, Mar 31] 요청하고 [Jan 1, Feb 15]만 캐시에 있다면 missing_ranges가 [Feb 16, Mar 31]만 반환해서 그 차분만큼만 DART API를 호출합니다. 두 테이블 분리(`disclosures` + `fetched_days`)가 핵심 — *0건짜리 날도 조회됨*으로 마킹해야 다음에 재호출이 안 되니까요. 오늘 날짜는 영구 마킹 대상에서 제외 — 장중 추가되는 공시를 놓치지 않으려고."

### 4. Tool description = LLM 라우팅 프롬프트 — "회귀 방지까지"
> "Tool description은 단순 docstring이 아니라 LLM이 도구를 *언제 부를지/안 부를지* 결정하는 프롬프트입니다. 그래서 *사용 시점 / 사용하지 않을 때 → 형제 tool 명시* 형식을 강제했고, 도구 3개가 서로를 cross-reference 합니다. 가장 중요한 건 이 cross-reference가 자동 회귀 테스트로 묶여있다는 점입니다 — 누가 description 다듬다가 형제 tool 이름을 실수로 빼면 테스트가 깨집니다. *Tool description의 프롬프트 엔지니어링은 코드처럼 회귀 가능한 자산* 이라는 게 제 결론이었습니다."

### 5. 의도적 제외 — "안 한 것이 곧 trade-off"
> "Decisions.md에 *안 한 것* 표를 명시적으로 둔 이유는, 안 한 것을 모르는 채 안 한 것과 알면서 안 한 것이 다르기 때문입니다. 대표 예: LLM provider 추상화 — MCP가 이미 그 추상화고 위에 또 올리면 군더더기. HTTP transport — 사이드 프로젝트엔 stdio가 적합하고 FastMCP가 한 줄로 전환 가능. PyPI publish — 유지보수 의무 부담이 사이드 프로젝트엔 과해서 uvx-from-git이 적정점. 한경컨센서스 스크래퍼 — ToS 회색지대라 합법 대체(KCMI/KIF/KIET)를 권장. *알면서 멈춘 trade-off*는 지표라 생각합니다."

---

## 5. 채용 공고 키워드 — 시스템 매핑

공고에 적힌 키워드가 시스템의 어느 부분과 매칭되는지:

| 공고 키워드 | 시스템 매핑 |
|---|---|
| LLM 기반 서비스 개발 | 3 MCP 도구가 Claude/GPT의 직접 호출 대상 |
| AI 에이전트 | MCP tool routing (LLM이 자연어 → 도구 자동 선택) |
| RAG 파이프라인 | search_research_reports (협의 RAG) + 시스템 전체 (Hybrid RAG) |
| PB/리서치 업무 지원 LLM Assistant | 단일 종목 종합 브리핑 시나리오로 직접 답변 |
| 프롬프트 엔지니어링 | Tool description의 cross-reference + 자동 회귀 검증 |
| 사내 데이터와 LLM 연동 백엔드 API | MCP 서버가 그 백엔드 (3 데이터 레이어를 단일 인터페이스로) |
| **MCP 기반 커넥터** | 정확히 매칭 — 가장 희소한 키워드 |
| 금융 도메인 | DART(공시) + ECOS(한국은행 거시) + 한국어 PDF, 한국 금융 데이터 표준 소스 |

---

## 6. 링크

- **Repository**: https://github.com/LChoiSH/mcp-finance-assistant
- **Decisions.md** (설계 결정 SSOT): [Decisions.md](Decisions.md)
- **architecture.md** (다이어그램 6종): [architecture.md](architecture.md)
- **README** (설치/사용): [README.md](README.md)
- **빠른 시연 명령**:
  ```bash
  claude mcp add finance-mcp-assistant -s user \
    --env DART_API_KEY=<dart키> \
    --env ECOS_API_KEY=<ecos키> \
    -- uvx --from git+https://github.com/LChoiSH/mcp-finance-assistant.git finance-mcp-server
  ```

---

## 7. 사용 예시 (시연 시나리오)

면접관/리뷰어가 *"어떻게 쓰는 건가?"* 물으면 답할 수 있는 시나리오:

| 질의 | 자동 호출되는 도구 |
|---|---|
| "삼성전자 2025년 1분기 공시 주요 흐름" | get_dart_disclosures |
| "한국 기준금리 2024년 월별 추이" | get_ecos_data |
| "리서치가 본 반도체 업황 전망" | search_research_reports |
| "삼성전자 자기주식 매수 시기와 그때 기준금리" | get_dart_disclosures + get_ecos_data |
| "PB가 고객에 줄 단일 종목 종합 브리핑" | 3개 도구 모두 |

---

## 8. 한 문장 요약 (가장 짧은 버전)

> "MCP 위에서 한국 금융 데이터 3종을 LLM에 통합 — Hybrid RAG와 incremental cache, 자동 회귀 가능한 tool description 프롬프트가 핵심."
