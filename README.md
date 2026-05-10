# finance-mcp-assistant

Korean finance-domain MCP server: research-report RAG + DART disclosures + ECOS macro indicators.

Design rationale: [Decisions.md](Decisions.md) · Build schedule: [Plan.md](Plan.md)

## Setup

```bash
uv sync
cp .env.example .env  # fill in OPENAI_API_KEY, DART_API_KEY, ECOS_API_KEY
```

## Run

```bash
uv run python server.py
```

The server speaks MCP over stdio — the client (Claude Desktop / Cursor / Inspector) owns the process.

## Debug with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run python server.py
```
