# ARCHITECTURE

`finance-mcp-assistant`는 **3개의 데이터 레이어**를 단일 MCP 서버로 묶고, 각 레이어를 별도 MCP tool로 노출합니다. 이 구조가 시스템의 중심 아이디어입니다.

설계 근거: [Decisions.md](Decisions.md) · 사용 시나리오: [README.md](README.md)

---

## 1. 시스템 개요

```mermaid
flowchart LR
    User["사용자"]
    Client["MCP Client<br/>(Claude Code / Desktop / Cursor)"]

    subgraph Server["server.py · FastMCP · stdio"]
        T1["search_research_reports"]
        T2["get_dart_disclosures"]
        T3["get_ecos_data"]
    end

    Chroma[("Chroma<br/>+ bge-m3")]
    SQLite[("SQLite<br/>cache-aside")]
    DART[/"DART OPEN API"/]
    ECOS[/"한국은행 ECOS API"/]

    User --> Client
    Client <-->|"JSON-RPC<br/>over stdio"| Server

    T1 --> Chroma
    T2 --> SQLite
    SQLite -.miss.-> DART
    T3 --> ECOS

    style Client fill:#e1f5ff
    style Server fill:#fff4e1
```

**핵심**:
- 클라이언트가 우리 서버 프로세스를 자식으로 spawn → stdin/stdout으로 JSON-RPC 송수신 (네트워크 포트 없음)
- 서버는 LLM을 직접 호출하지 않음 — LLM은 클라이언트 책임. 우리는 *도구만 제공*
- 도구 3개는 모두 독립. 조합은 클라이언트 LLM이 결정 (다이어그램 4 참조)

---

## 2. 3 데이터 레이어 — 변동성/접근 패턴별 차등 정책

```mermaid
flowchart TB
    subgraph L1["Layer 1 — 사전 인덱싱 비정형"]
        direction LR
        L1T["search_research_reports"] --> L1S[("Chroma<br/>+ bge-m3 임베딩")]
        L1Note["불변 PDF · 일회 인덱싱"]
    end

    subgraph L2["Layer 2 — 캐싱되는 정형"]
        direction LR
        L2T["get_dart_disclosures"] --> L2S[("SQLite<br/>cache-aside")]
        L2S -.miss only.-> L2A[/"DART API"/]
        L2Note["과거: 불변 / 오늘: mutating"]
    end

    subgraph L3["Layer 3 — 실시간 호출 정형"]
        direction LR
        L3T["get_ecos_data"] --> L3A[/"ECOS API"/]
        L3Note["월/분기 갱신 · 호출 빈도 ↓"]
    end

    style L1Note fill:none,stroke:none
    style L2Note fill:none,stroke:none
    style L3Note fill:none,stroke:none
```

| Layer | 변동성 | 호출 빈도 | 저장 전략 | 이유 |
|---|---|---|---|---|
| 1. 리서치 리포트 | 불변 | (인덱싱 1회) | 사전 임베딩 → 벡터 검색 | 의미 검색 = 벡터 외 대안 약함 |
| 2. DART 공시 | 과거 불변 / 오늘 변경 | 자주 | cache-aside (incremental) | 외부 API 비용/지연 최소화 |
| 3. ECOS 거시 | 월/분기 갱신 | 적음 | 직접 호출, 캐시 없음 | ROI 낮음 (호출량 적고 데이터량 작음) |

**모든 데이터를 동일하게 다루지 않는다**가 핵심 — Decisions.md §7 참조.

---

## 3. Cache-aside 내부: incremental day coverage

이게 단순 hit/miss와 다른 부분입니다. 한 번의 요청 안에서 캐시에 *부분적으로 있는 경우* 빠진 부분만 DART를 부릅니다.

```mermaid
sequenceDiagram
    autonumber
    participant Tool as get_dart_disclosures
    participant Repo as DartRepository
    participant DB as SQLite
    participant DART as DART API

    Tool->>Repo: missing_ranges(corp, [Jan 1, Mar 31])
    Repo->>DB: SELECT rcept_dt FROM fetched_days
    DB-->>Repo: covered = {Jan 1 .. Feb 15}
    Repo-->>Tool: missing = [(Feb 16, Mar 31)]

    Note over Tool: 빠진 구간만 fetch

    Tool->>DART: search_disclosures(Feb 16, Mar 31)
    DART-->>Tool: rows

    Tool->>Repo: save_disclosures(rows, Feb 16, Mar 31)
    Repo->>DB: UPSERT disclosures
    Repo->>DB: INSERT fetched_days (오늘 제외)

    Tool->>Repo: find_disclosures([Jan 1, Mar 31])
    Repo->>DB: SELECT * WHERE corp=? AND date BETWEEN
    DB-->>Tool: 전 구간 rows
```

**두 테이블 분리가 핵심**:
- `disclosures` — 실제 공시 행
- `fetched_days` — *그 날을 한 번이라도 호출했는가* 플래그 (코드와 날짜 페어)

**왜 두 테이블?** 0건짜리 날도 *"조회됨"* 으로 마킹해야 다음에 재호출 안 하니까. *"행 존재 = 조회됨"* 으로 추론 불가.

**오늘은 영구 마킹 제외**: 장중 추가 공시 가능성 → save 시 오늘 날짜는 fetched_days에 안 넣음 → 다음 호출 시 항상 fresh fetch.

---

## 4. Tool routing — 도구는 독립이지만 LLM이 묶음

```mermaid
flowchart TB
    Q["사용자: '삼성전자 분석 + 금리 영향'"]
    LLM["Client LLM<br/>(Claude)"]

    Q --> LLM

    subgraph Visible["LLM에게 보이는 3개 description"]
        D1["search_research_reports<br/>━━━<br/>사용 시점: 분석/전망/투자의견<br/>else: → get_dart_disclosures<br/>else: → get_ecos_data"]
        D2["get_dart_disclosures<br/>━━━<br/>사용 시점: 공시 자료<br/>else: → search_research_reports<br/>else: → get_ecos_data"]
        D3["get_ecos_data<br/>━━━<br/>사용 시점: 금리/환율/GDP<br/>else: → get_dart_disclosures<br/>else: → search_research_reports"]
    end

    LLM -->|"'분석' 매칭"| D1
    LLM -->|"'금리' 매칭"| D3
    LLM -.->|skip| D2

    D1 --> R1["chunks"]
    D3 --> R2["시계열"]
    R1 --> Final["LLM이 합성 → 답변"]
    R2 --> Final
```

**Tool description = LLM 라우팅의 프롬프트.** Decisions.md §9의 핵심:
- "사용 시점" + "사용하지 않을 때 → 형제 tool 명시" 형식
- 형제 tool 이름이 들어가는지 자동 검증 (테스트 `test_descriptions_cross_reference_each_other`)
- 면접 답변: *"tool description은 단순 문서가 아니라 LLM의 routing 프롬프트. cross-reference로 정확도를 높였고 테스트로 회귀 방지까지"*

---

## 5. Lazy import — stdio MCP의 운영적 특성

```mermaid
flowchart LR
    Spawn["client spawn<br/>server.py"]
    Import["module import"]
    Tool["tool 호출"]

    Spawn --> Import
    Import -->|fast path| Ready["server ready"]
    Ready -->|"tool 호출 시"| Tool
    Tool -.->|"첫 호출 시 lazy"| Heavy["torch + bge-m3 load<br/>(~5s + 모델 다운로드)"]

    style Heavy fill:#ffe0e0
    style Ready fill:#e1ffe1
```

**stdio = 매 클라이언트 spawn마다 fresh 프로세스.** Eager import 시 서버 startup 25초 → UX 직격타.

대응: `rag/embedding.py`에서 `torch`, `HuggingFaceEmbedding`을 함수 본문 안에서 import. 결과:
- 모듈 import: 35s → **2.87s**
- DART/ECOS 도구만 쓰는 사용자는 ML 의존성 끝까지 안 끌어들임

상세: Decisions.md §13.

---

## 6. 의도적 제외

다이어그램에 안 나타나는 것들 — **있어 보이는데 일부러 안 만든 것**:

- **자체 LLM provider 추상화** — MCP가 이미 그 추상화. 위에 올리면 군더더기 (§3)
- **자체 임베딩 추상화 레이어** — LlamaIndex `BaseEmbedding`이 표준. 위에 올리면 같은 패턴 (§6)
- **HTTP transport** — 사이드 프로젝트엔 stdio 적합. FastMCP가 한 줄로 전환 가능 (§2)
- **OAuth/스코프** — HTTP 갈 때 같이 검토 (§14)

전체 목록: Decisions.md "안 한 것" 표.

---

## 부록: 코드 위치

| 다이어그램 요소 | 파일 |
|---|---|
| MCP 서버 + tool 등록 | `server.py` |
| 3 tool 함수 | `tools/disclosures.py`, `tools/research.py`, `tools/macro.py` |
| DART/ECOS 클라이언트 | `clients/dart.py`, `clients/ecos.py` |
| Cache-aside repository | `storage/repository.py` |
| SQLite 스키마 | `storage/db.py` |
| RAG 파이프라인 | `rag/{embedding,indexer,retriever}.py` |
| 환경 설정 | `config.py` (.env 로드 + 로거 silence + 키 마스킹) |
