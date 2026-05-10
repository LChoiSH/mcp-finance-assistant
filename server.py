"""finance-mcp-assistant — MCP server entry point.

Stdio transport. Invoke via:
    uv run python server.py
or for debugging:
    npx @modelcontextprotocol/inspector uv run python server.py
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from tools.disclosures import get_dart_disclosures
from tools.macro import get_ecos_data
from tools.research import search_research_reports

mcp = FastMCP("finance-mcp-assistant")
mcp.tool()(get_dart_disclosures)
mcp.tool()(search_research_reports)
mcp.tool()(get_ecos_data)


def main() -> None:
    """Console-script entry point used by `uvx finance-mcp-server`."""
    mcp.run()


if __name__ == "__main__":
    main()
