# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

This repo is **pre-implementation**. It currently contains only two planning documents:

- `Decisions.md` — the SSOT (single source of truth) for design decisions and their rationale. Read this before suggesting any architectural change; every choice has explicit "이유" (reason), "검토한 대안" (alternatives considered), and "한계" (limits) sections that you should respect or explicitly challenge.
- `Plan.md` — 2-day build schedule with checkpoints, folder layout, and risk mitigations.

The project is a side project named **finance-mcp-assistant**, scoped to match a Korean finance-domain "AI Application Developer / LLM Service Developer" job posting. Optimization target is **interview defensibility**, not production readiness — when in doubt, keep `Decisions.md` and the diagram tight rather than adding code.

## Planned commands (uv-based)

The project will use `uv` (Astral) as the package manager. Once `pyproject.toml` exists:

```bash
uv sync                              # install deps from uv.lock
uv run python server.py              # run the MCP server (stdio)
uv run python scripts/index_pdfs.py  # build the Chroma index from data/pdfs/
npx @modelcontextprotocol/inspector uv run python server.py  # debug MCP tools
```

Single-test invocation is not formalized yet — `Plan.md` only calls for "간단한 동작 확인 스크립트" under `tests/`. If you add a real test runner, prefer `uv run pytest tests/<file>.py::<test>`.

## Architecture: three data layers (the core design)

Every data path in this project is one of these three layers. The **differentiation** of the project is that each layer uses a different storage strategy chosen by data volatility and access pattern — do not collapse them into a single uniform interface.

| Layer | Source | Storage | Why |
|---|---|---|---|
| Pre-indexed unstructured | Korean research-report PDFs (한경컨센서스) | LlamaIndex → Chroma (local file) | RAG over static documents |
| Cached structured | DART disclosures (공시) | SQLite, **cache-aside** with incremental range fetch | Past disclosures are immutable; today's grow → differential TTL |
| Live structured | ECOS macro indicators (한국은행) | Direct API call, no cache | Low call frequency, monthly/quarterly updates → caching ROI is low |

Three MCP tools map 1:1 onto these layers:

- `search_research_reports` → RAG layer
- `get_dart_disclosures` → DART cache layer
- `get_ecos_data` → ECOS direct call

This 3-layer split is the answer to "왜 이렇게 설계했나" interview questions. Treat it as load-bearing.

## Architecture: MCP boundary

- Transport is **stdio**, not HTTP. The client (Claude Desktop / Cursor / Inspector) owns the server process lifecycle. API keys live in local `.env`.
- **No LLM provider abstraction layer.** This is intentional — `Decisions.md` §3 argues MCP itself *is* the LLM-tool abstraction, so adding a Strategy/adapter on top is redundant. Do not add one without updating `Decisions.md`.
- **Tool descriptions are prompt engineering**, not docstrings. Each tool's description must spell out *when to use* and *when not to use* (pointing at the other tool). See `Decisions.md` §9 for the required template — follow it for every new tool.

## Planned folder structure

`Plan.md` proposes this layout. Match it unless there's a reason not to:

```
server.py                # MCP server entrypoint
tools/{research,disclosures,macro}.py   # one file per MCP tool
clients/{dart,ecos}.py                  # external API clients
rag/{indexer,retriever}.py              # LlamaIndex wrappers
storage/{db,models,repository}.py       # SQLite + Pydantic + DART Repository
scripts/index_pdfs.py                   # one-shot PDF indexer
data/{pdfs,chroma,cache.db}             # all gitignored
```

## Stack choices (locked unless `Decisions.md` is updated)

- Python 3.11+, `uv` for env/deps, `httpx` (async) for HTTP, `pydantic` for validation.
- RAG: LlamaIndex + Chroma + bge-m3 (local via `llama-index-embeddings-huggingface`, 1024-dim, MPS-accelerated on Apple Silicon).
- Cache: SQLite, cache-aside with incremental range filling (not naive hit/miss).

If you propose swapping any of these, update the matching section in `Decisions.md` in the same change — the document's value is that it stays consistent with the code.

## Things to deliberately NOT add

`Decisions.md` has an explicit "안 한 것" (intentionally excluded) table. Do not silently add: an LLM provider abstraction, an OpenAI provider implementation, LangChain, a managed vector DB (Pinecone), ECOS caching, RAGAS-style answer-quality metrics, or PII masking. Each is excluded for a stated reason — re-introducing one needs the reason to change first.

## Working language

Both planning docs are in Korean. New decisions, comments, and commit messages should match the existing language of the file being edited. `Decisions.md` is Korean → keep it Korean.
