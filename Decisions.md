# DECISIONS

이 프로젝트의 핵심 설계 결정과 그 근거. 면접 답변의 일관된 근거가 되는 단일 출처(SSOT).

---

## 프로젝트 목적

채용 공고: "AI Application Developer / LLM Service Developer (3년차)" 매칭용 사이드 프로젝트.

공고 키워드:
- LLM 기반 서비스 개발 (Claude, GPT 등)
- AI 에이전트 및 RAG 파이프라인
- PB/리서치 업무 지원용 AI Assistant
- 프롬프트 엔지니어링
- 사내 데이터와 LLM 연동을 위한 백엔드 API
- **MCP 기반 커넥터 개발 및 운영** ← 가장 희소한 매칭 키워드
- 금융 도메인

산출물 우선순위 (데모 시연 없는 면접 환경):
1. 코드 동작 (본인 검증용)
2. **DECISIONS.md (이 문서)**
3. 아키텍처 다이어그램
4. README 간결하게

---

## 시스템 개요
사용자
↓
[MCP Client (Claude Desktop / Cursor / Inspector)]
↓ MCP 프로토콜 (stdio)
[MCP Server]
├─ search_research_reports → LlamaIndex + Chroma (RAG)
├─ get_dart_disclosures    → SQLite Cache → DART API
└─ get_ecos_data           → ECOS API (직접 호출)

데이터 레이어 3종:
1. **사전 인덱싱 비정형** — 리서치 PDF (Chroma)
2. **캐싱되는 정형** — DART 공시 (SQLite, cache-aside)
3. **실시간 호출 정형** — ECOS 거시 지표

---

## 결정 1: MCP 도입

### 선택
Python MCP SDK + stdio transport.

### 이유
- 공고 명시 키워드 직접 매칭
- LLM-도구 분리 표준 프로토콜 (Anthropic, OpenAI, Google, Microsoft 채택)
- 한 번 만든 도구를 모든 MCP 호환 클라이언트에서 재사용

### 본질 인식
MCP는 새 발명이 아니라 **LLM-도구 통합 패턴의 컨벤션화**. REST API + Function Calling으로도 동일 동작 구현 가능. MCP가 표준화한 것: 도구 정의 스키마, 호출 메시지 형식, 도구 발견 절차(`tools/list`), 에러 처리.

비유: HTTP가 TCP 위에 메시지 형식을 표준화했듯, MCP는 LLM-도구 통합의 컨벤션을 통일.

### 검토한 대안
- **OpenAI Function Calling**: provider 종속, 표준 아님
- **LangChain Tools**: 라이브러리 추상화, 프로토콜 아님
- **자체 REST API + LLM에 명세 전달**: MCP 등장 전 표준 방식, 단일 클라이언트라면 더 단순

### 한계
- Stateful long-running, 대용량 스트리밍 약함
- 인증/권한 모델 발전 중
- 단일 LLM/단일 클라이언트 환경에선 오버킬 가능
- 프로토콜 오버헤드로 함수 직접 호출 대비 약간의 latency

### 면접 체크포인트
- "MCP는 Claude 전용?" → 오픈 표준, 주요 LLM/도구 모두 채택
- "REST API와 차이?" → 자기 기술(self-describing), 메시지 형식 표준화, runtime 사용
- "함수 직접 호출과 차이?" → 동작 같음. 차이는 책임 분리, 재사용성, 동적 발견. **사이드 프로젝트 단독에선 가치 잠재적, 회사 환경(N개 클라이언트 × M개 도구)에서 발현**

---

## 결정 2: stdio transport (vs HTTP)

### 선택
stdio.

### 이유
- 사이드 프로젝트, 호스팅 불필요
- API key 로컬 .env 관리 단순
- 클라이언트가 프로세스 라이프사이클 관리
- 외부 노출 없어 신뢰 경계 명확

### 확장 시
- 다중 사용자 → HTTP transport 전환
- OAuth/scope 기반 권한 추가
- 호스팅 인프라 (Cloudflare Workers, AWS 등)

---

## 결정 3: LLM Provider 추상화 안 함

### 선택
직접 추상화 레이어 만들지 않음.

### 이유
- MCP 표준에 충실: LLM 호출은 클라이언트 책임, 서버는 도구 제공만
- MCP 자체가 LLM-도구 추상화의 표준 답이라, 추가 추상화는 군더더기
- 강제로 끼워넣으면 "왜 거기서 필요?" 질문에 답이 약함

### 면접 체크포인트
- "Provider 추상화 안 했네?" → "MCP 표준에 충실. 클라이언트가 LLM 호출 담당. 자체 LLM 클라이언트를 만든다면 Strategy 패턴으로 추상화 레이어 둘 것 — 게임 개발의 광고 SDK 추상화와 같은 원리"

---

## 결정 4: RAG 파이프라인 = LlamaIndex

### 선택
LlamaIndex로 PDF 로딩/청킹/임베딩/검색 통째로 처리.

### 이유
- RAG는 청킹/임베딩/검색이 검증된 패턴 → 직접 짜는 학습 가치 낮음
- 차별화 영역(MCP 통합, 캐싱, tool description)에 시간 집중
- vector store backend 추상화 내장 (Chroma → Pinecone 교체 1줄)

### 검토한 대안
- **LangChain RAG**: 본체 의존성 큼, MCP 어필과 충돌
- **직접 구현**: 청킹 알고리즘/임베딩/벡터DB 연동 모두 작성 → 2일에 과부하
- **Haystack**: 한국 레퍼런스 적음

### 한계
- PDF 표 구조 보존 약함 (리서치 리포트 실적 표 검색 품질 ↓)
- 프로덕션이면 표는 별도 파서로 추출해 구조화 데이터로 저장하는 하이브리드 고려

### 면접 답변
"RAG는 검증된 패턴이라 LlamaIndex로 빠르게 구축. 차별화 영역인 MCP 통합과 데이터 라이프사이클 설계에 시간을 집중하는 판단. 모든 걸 직접 짜는 게 학습엔 좋지만, 프로덕트 관점에선 어디에 시간을 쓸지가 더 중요."

---

## 결정 5: 벡터 DB = Chroma

### 선택
Chroma (로컬 파일 기반).

### 이유
- 단일 파일, Docker/별도 서버 불필요 → 재현 가능성 ↑
- LlamaIndex 통합 좋음
- 25 PDF / 수백 청크 규모에 충분

### 검토한 대안
- **Pinecone/Weaviate**: 매니지드 클라우드, 회원가입 필요 → 사이드 프로젝트 부적합
- **FAISS**: 빠르지만 메타데이터 관리 직접 짜야 함
- **pgvector**: Postgres 띄워야 함, 오버킬

### 한계
- 동시성/대용량 부적합
- 프로덕션이면 pgvector(RDB 통합) 또는 Pinecone 고려

---

## 결정 6: 임베딩 모델 = bge-m3 (로컬)

### 선택
BAAI/bge-m3 (1024차원), `llama-index-embeddings-huggingface` 경유 로컬 추론. Apple Silicon이면 MPS 가속.

### 이유
- **외부 API 의존성 0** — 사이드 프로젝트의 자족성(self-contained) 우선
- **데모 환경 자유도** — 키 발급 / 빌링 / 네트워크 연결 가정 없이 동작
- **한국어 품질** — MTEB 한국어 벤치에서 OpenAI text-embedding-3-small 대비 약간 우수
- LlamaIndex `BaseEmbedding` 인터페이스라 추후 한 줄로 OpenAI/Voyage 교체 가능

### 검토한 대안
- **OpenAI text-embedding-3-small**: 인덱싱 비용 ~$0.02 사실상 무료, 단순. **다만 OpenAI 가입 필요 = 외부 의존성 +1.** 데모 자족성보다 비용·속도가 더 중요한 케이스에서 합리적.
- **Voyage AI multilingual-2**: Anthropic 공식 권장 임베딩 파트너, 한국어 우수. 가입 필요한 건 OpenAI와 같음.
- **Upstage Solar Embedding**: 한국어 특화. 키 추가 발급 = 외부 의존성 +1.
- **OpenAI text-embedding-3-large**: 정밀도 ↑, 비용 6.5배. 25 문서 규모엔 차이 미미.

### 한계
- 모델 1회 다운로드 ~2.3GB (`~/.cache/huggingface/`)
- torch + sentence-transformers 트랜지티브 의존성 ~1.5GB
- CPU 인덱싱 시 25 PDF 5~15분 / Apple MPS 2~5분 (OpenAI는 1~2분)
- 도메인 특화 fine-tuning 없음 (모든 옵션 공통)

### 면접 답변
"원래 OpenAI 임베딩 후보였는데, 사이드 프로젝트 단계에선 외부 의존성을 0개로 가져갈 수 있는 자족성이 더 가치 있다고 판단해 bge-m3 로컬 모델로 전환했습니다. 한국어 품질도 약간 더 나오고요. 단 인덱싱 시간이 늘어나는 trade-off는 인지하고 있고, 프로덕션이면 인덱싱 빈도와 GPU 가용성에 따라 다시 평가할 영역입니다. 임베딩 모델 자체는 LlamaIndex의 BaseEmbedding 인터페이스 위에 있어서 한 줄로 갈아끼울 수 있게 격리해뒀습니다."

---

## 결정 7: DART 캐싱 (cache-aside) — ECOS는 직접 호출

### 선택
DART 공시는 SQLite에 cache-aside 패턴으로 저장. ECOS는 매번 직접 호출.

### 이유 (차등 적용)

| 데이터 | 변동성 | 호출 빈도 | 결정 |
|---|---|---|---|
| DART 공시 (과거) | 불변 | 자주 | 캐싱 |
| DART 공시 (오늘) | 추가됨 | 자주 | 캐싱 (짧은 TTL) |
| ECOS 거시 지표 | 월/분기 갱신 | 적음 | 직접 호출 |

핵심: **데이터 성격별 차등 정책.** 모든 데이터를 동일하게 다루지 않음.

### 구현 패턴
- Repository 클래스 (find / save)
- Incremental caching: 누락된 날짜 범위만 재호출

### 한계
- 단일 SQLite, 동시성 부적합
- 정밀한 invalidation 없음 (TTL 기반)

### 면접 답변
"외부 API 비용/지연 최소화를 위해 DART 공시에 cache-aside 패턴 적용. 단순 hit/miss가 아니라 incremental caching으로 누락 범위만 재호출. ECOS는 호출 빈도와 데이터 양 고려해 캐싱 대상에서 제외 — 데이터 성격별 차등 정책이 핵심."

---

## 결정 8: 외부 데이터 = DART + ECOS

### 선택
DART OPEN API (공시) + 한국은행 ECOS API (거시 지표).

### 이유
- 공식 무료 API
- 한국 금융 데이터 표준 소스
- 공고가 한국 회사 + 금융 도메인 → 한국 데이터 적합
- PB/리서치 업무에서 가장 자주 참조

### 검토한 대안
- **yfinance/Alpha Vantage**: 해외 위주, 도메인 어긋남
- **Bloomberg/FnGuide**: 유료, 사이드 프로젝트 부적합

---

## 결정 9: Tool description 정성껏 작성 (프롬프트 엔지니어링)

### 핵심
Tool description은 LLM이 도구를 선택하는 유일한 근거. 단순 설명이 아니라 **언제 쓰고 언제 안 쓰는지**까지 명시.

### 패턴
```python
"""
[도구 목적 한 줄]

사용 시점:
- ...
- ...

사용하지 않을 때:
- ... (다른 tool 안내)

Args:
    ...
"""
```

### 면접 답변
"Tool description은 LLM의 도구 라우팅을 결정하는 프롬프트. '언제 쓰고 언제 안 쓰는지'까지 명시해 라우팅 정확도를 높였다. 사실상 tool routing의 프롬프트 엔지니어링."

---

## 결정 10: 패키지 매니저 = uv

### 선택
uv (Astral).

### 이유
- pip 대비 10~100배 빠름
- uv.lock 재현성
- Python 버전 관리 통합
- 2024~2025 표준화 흐름

---

## 결정 11: HTTP 클라이언트 = httpx

### 선택
httpx (async 지원).

### 이유
- MCP SDK가 async 기반 → 자연스러운 통합
- DART/ECOS 동시 호출 시 응답 시간 절감

### 운영 디테일 (구현 중 발견)
httpx의 기본 INFO 로그는 요청 URL 전체를 찍습니다. ECOS는 path-based REST라 **API 키가 URL에 포함**됩니다 — 로그/스크린샷 외부 공유 시 키 노출 리스크. 대응:
1. `config.py`에서 `httpx`/`httpcore` 로거를 WARNING으로 silence
2. 우리 클라이언트(`clients/dart.py`, `clients/ecos.py`) 자체 INFO 로그에서 키를 `***`으로 마스킹

이건 *로깅도 보안 경계*라는 일반 원칙의 적용. 면접에서 "로깅 어떻게 하셨나" 류 질문에 구체적 답변.

---

## 결정 12: 데이터 검증 = Pydantic

### 선택
Pydantic.

### 이유
- LLM 응답/외부 API 응답의 런타임 검증
- MCP SDK 내부적으로 사용 → 통합 자연스러움

---

## 결정 13: Lazy import for stdio MCP startup

### 핵심
`torch`, `sentence-transformers`, `HuggingFaceEmbedding`은 **함수 본문 안에서 import**. 모듈 top-level이 아님.

### 이유
**stdio transport의 본질**: 클라이언트가 매번 자식 프로세스를 spawn → 매 세션마다 startup 비용을 새로 지불. 만약 서버 모듈 import에 25초가 걸리면 (= eager torch import) 사용자 입장에선 *MCP 서버 응답 느림*으로 직접 체감.

측정값:
- Eager torch import: pytest collection 35초
- Lazy import (현재): pytest collection 2.87초

### 적용 범위
- `rag/embedding.py`의 `_detect_device()`, `get_embed_model()` 둘 다 함수 안에서 torch/HuggingFace import
- DART/ECOS 도구는 검색 도구가 안 호출되는 한 무거운 의존성을 끌어들이지 않음

### 면접 답변
"임베딩 도구는 결과적으로 ML 모델을 끌어와야 하지만, stdio MCP 서버는 매 세션 fresh 프로세스이기 때문에 startup이 UX 직격타입니다. 모듈 import 시점이 아닌 도구 호출 시점에 모델을 로드하도록 lazy import 패턴을 적용했고, 결과적으로 startup이 ~12배 빨라졌습니다. 이건 stdio MCP의 운영적 특성을 인지한 결정이고, HTTP transport였다면 이 trade-off는 다르게 갔을 것입니다."

---

## 결정 14: Distribution = GitHub repo + uvx-from-git

### 선택
GitHub public repo로 publish, 사용자는 `uvx --from git+https://github.com/<user>/finance-mcp-assistant.git finance-mcp-server` 한 줄로 실행.

### 이유
- **사용자 경험**: clone 없이 한 줄 실행 = 마찰 최소
- **유지보수 부담 0**: PyPI publish는 버전 관리 / changelog / yanking 의무가 따라옴, 사이드 프로젝트엔 과함
- **재현성**: git tag/commit으로 정확한 버전 고정 가능
- **uvx 가 환경 격리까지 처리**: 별도 venv 관리 불필요

### 검토한 대안
- **Clone-only (clone + uv sync + uv run)**: 가장 honest, 하지만 사용자가 4단계 거쳐야 함
- **PyPI (`uvx finance-mcp-assistant`)**: 가장 짧음. 단 유지보수 의무 + 면접에서 *"publish하고 안 쓰는 거 아닌가"* 디스카운트 가능
- **Docker**: 의존성 격리 완벽. 단 사용자에게 docker 설치 강제 + 이미지 호스팅 부담

### 한계
- API key는 사용자 본인 발급 (DART 무료 가입 / ECOS 무료 가입) — 이건 어떤 distribution이든 피할 수 없음
- 첫 검색 시 bge-m3 ~2.3GB 자동 다운로드 — 네트워크/디스크 비용 있음
- PDF는 사용자 자신 데이터 — distribution 대상 아님
- **uvx 모드 캐시 비영속**: uvx는 매 실행 시 임시 디렉토리에 격리 설치 → `data/cache.db` 와 `data/chroma/`도 임시 위치 → 세션 종료 시 소실. 같은 쿼리 반복 시 DART 재호출. 해결 = `config.py`에서 `CACHE_DB`/`CHROMA_DIR`을 `~/.cache/finance-mcp-assistant/`로 변경 (~30분 작업, 현재 deferred).
- **uvx 모드 RAG 미지원**: 위 이유 + PDF 디렉토리도 임시 → 인덱스 만들어도 곧 사라짐. RAG는 로컬 clone 모드 (시나리오 B) 권장. uvx에서도 쓰려면 PDF 디렉토리/Chroma 경로 외부화 필요.

### 진입점 구조
- `pyproject.toml [project.scripts]`: `finance-mcp-server = "server:main"`
- `server.py`에 `main()` 함수 (= `mcp.run()` 래퍼)

---

## 안 한 것 (의도적 제외)

| 항목 | 안 한 이유 |
|---|---|
| LLM Provider 추상화 | MCP 표준이 그 역할. 강제 도입 시 어색 |
| OpenAI Provider 구현 | Provider 추상화 안 하므로 불필요 |
| LangChain | LLM/Agent 추상화가 MCP와 충돌 |
| Pinecone/매니지드 벡터 DB | 회원가입 의존, 재현성 ↓ |
| HTTP transport (현재) | 사이드 프로젝트 = stdio 적합. FastMCP가 transport 추상화하므로 한 줄로 전환 가능 |
| OAuth/스코프 인증 | HTTP transport 갈 때 같이 검토할 영역 |
| 데모 영상 / 라이브 시연 자동화 | 면접 환경에서 시연 안 함 — Decisions.md / architecture / README가 산출물 |
| ECOS 캐싱 | 호출 빈도 낮고 데이터 양 작아 ROI 낮음 |
| 답변 평가 메트릭 (RAGAS 등) | 프로덕션 영역, 사이드 프로젝트 범위 초과 |
| PII 마스킹 | 사이드 프로젝트 범위 초과 (실무 필수임은 인지) |
| PyPI publish | 유지보수 의무 (changelog/yank/depr) 비대비 ROI 낮음. uvx-from-git이 적정점 |
| 한경컨센서스 자동 스크래퍼 | ToS 회색지대, 면접에서 마이너스 가능. 합법 대체 (KCMI/KIF/KIET) 권장 |
| 자체 임베딩 추상화 레이어 | LlamaIndex BaseEmbedding이 이미 표준 인터페이스. 추상화 위에 추상화 = 군더더기 |

---

## 면접 답변 종합 메시지

> "기술 선택의 원칙은 두 가지였습니다.
> 
> **첫째, 차별화 가치가 있는 영역은 직접 구현.** MCP 서버 설계, 데이터 라이프사이클(캐싱), tool description 프롬프트 엔지니어링.
> 
> **둘째, 검증된 패턴은 라이브러리 활용.** RAG 파이프라인은 LlamaIndex.
> 
> 모든 걸 직접 짜는 게 학습엔 의미 있지만, 프로덕트 관점에선 어디에 시간을 집중할지가 더 중요하다고 판단했습니다."

> "이 시스템은 세 가지 데이터 레이어를 가집니다.
> 1. 사전 인덱싱 비정형 데이터 — 리서치 리포트 (LlamaIndex + Chroma)
> 2. 캐싱되는 정형 데이터 — DART 공시 (SQLite, cache-aside)
> 3. 실시간 호출 정형 데이터 — ECOS 거시 지표
> 
> 데이터의 변동성과 접근 패턴에 따라 저장 전략을 다르게 가져간 게 핵심 설계 결정입니다."