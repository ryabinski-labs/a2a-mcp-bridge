"""Research MCP server (stdio).

Exposes the *tools* the Researcher agent uses to gather sources. Run directly
(``python -m a2a_mcp_bridge.mcp_servers.research_tools``) it speaks MCP over
stdio; the Researcher launches it as a subprocess.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import corpus

mcp = FastMCP("research-tools")


@mcp.tool()
def web_search(query: str, limit: int = 3) -> str:
    """Search the document corpus for a query and return ranked hits.

    Each line includes a ``doc_id:`` that can be passed to ``fetch_document``.
    """
    hits = corpus.search(query, limit=limit)
    if not hits:
        return f"No results for: {query!r}"
    lines = [f"Search results for {query!r}:"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"{i}. {hit['title']}  (doc_id: {hit['doc_id']}, score: {hit['score']})")
    return "\n".join(lines)


@mcp.tool()
def fetch_document(doc_id: str) -> str:
    """Fetch the full text of a document by its ``doc_id``."""
    doc = corpus.fetch(doc_id)
    if doc is None:
        return f"No document with doc_id {doc_id!r}."
    return f"# {doc['title']}\n(doc_id: {doc['doc_id']})\n\n{doc['body']}"


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
