"""
MCP Commands Server
Tracks AI command usage via MCP tools.
"""

import asyncio
import json
import os
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from mcp_commands.storage import (
    log_command,
    get_history,
    get_stats,
    search_commands,
    delete_command,
)

_transport = os.getenv("MCP_TRANSPORT", "stdio")
_host = "0.0.0.0" if _transport == "sse" else "127.0.0.1"
_port = int(os.getenv("MCP_PORT", "8000"))

mcp = FastMCP(
    name="mcp-commands",
    instructions=(
        "MCP server for tracking AI command usage. "
        "Use log_command to record commands used, and the other tools to query history & stats."
    ),
)


# ─────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────

@mcp.tool()
def log_command_tool(
    command: str,
    category: str = "",
    context: str = "",
) -> str:
    """
    Log one AI command usage.

    Args:
        command:  The command name, e.g. '/commit', '/recap', 'deep-research'
        category: Optional group, e.g. 'git', 'research', 'oracle', 'session'
        context:  Optional free-text note about where/why it was used
    """
    row_id = log_command(
        command=command,
        category=category or None,
        context=context or None,
    )
    return f"✅ Logged command '{command}' (id={row_id})"


@mcp.tool()
def get_history_tool(
    limit: int = 20,
    command: str = "",
    category: str = "",
) -> str:
    """
    Get recent command-usage history.

    Args:
        limit:    Max rows to return (default 20)
        command:  Filter by command name (partial match)
        category: Filter by category (exact match)
    """
    rows = get_history(
        limit=limit,
        command=command or None,
        category=category or None,
    )
    if not rows:
        return "No records found."
    return json.dumps(rows, ensure_ascii=False, indent=2)


@mcp.tool()
def get_stats_tool(top_n: int = 10) -> str:
    """
    Get command usage statistics.

    Args:
        top_n: How many top items to show per category (default 10)

    Returns JSON with:
    - total usage count
    - top commands ranked by usage
    - top categories ranked by usage
    - daily counts for the last 7 days
    """
    stats = get_stats(top_n=top_n)
    return json.dumps(stats, ensure_ascii=False, indent=2)


@mcp.tool()
def search_commands_tool(query: str, limit: int = 20) -> str:
    """
    Search command history by keyword.

    Searches across command name, category, and context fields.

    Args:
        query: Search keyword
        limit: Max results (default 20)
    """
    rows = search_commands(query=query, limit=limit)
    if not rows:
        return f"No records matching '{query}'."
    return json.dumps(rows, ensure_ascii=False, indent=2)


@mcp.tool()
def delete_command_tool(row_id: int) -> str:
    """
    Delete a command-usage record by its id.

    Args:
        row_id: The id field from history records
    """
    deleted = delete_command(row_id=row_id)
    if deleted:
        return f"🗑️ Deleted record id={row_id}"
    return f"⚠️ No record found with id={row_id}"


# ─────────────────────────────────────────────
# REST API (dashboard endpoints)
# ─────────────────────────────────────────────

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "service": "mcp-commands"})


@mcp.custom_route("/api/stats", methods=["GET"])
async def api_stats(request: Request) -> JSONResponse:
    top_n = int(request.query_params.get("top_n", "10"))
    stats = get_stats(top_n=top_n)
    return JSONResponse(stats)


@mcp.custom_route("/api/history", methods=["GET"])
async def api_history(request: Request) -> JSONResponse:
    limit = int(request.query_params.get("limit", "50"))
    command = request.query_params.get("command", "") or None
    category = request.query_params.get("category", "") or None
    rows = get_history(limit=limit, command=command, category=category)
    return JSONResponse(rows)


@mcp.custom_route("/api/search", methods=["GET"])
async def api_search(request: Request) -> JSONResponse:
    query = request.query_params.get("q", "")
    if not query:
        return JSONResponse({"error": "q parameter required"}, status_code=400)
    limit = int(request.query_params.get("limit", "20"))
    rows = search_commands(query=query, limit=limit)
    return JSONResponse(rows)


@mcp.custom_route("/api/live", methods=["GET"])
async def api_live(request: Request) -> StreamingResponse:
    """SSE stream that pushes new commands every 2 seconds."""
    async def event_stream():
        last_id = 0
        # Get initial max id
        history = get_history(limit=1)
        if history:
            last_id = history[0].get("id", 0)

        while True:
            await asyncio.sleep(2)
            new_rows = get_history(limit=20)
            fresh = [r for r in new_rows if r.get("id", 0) > last_id]
            if fresh:
                last_id = max(r.get("id", 0) for r in fresh)
                for row in reversed(fresh):
                    yield f"data: {json.dumps(row, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main():
    if _transport == "sse":
        mcp.run(transport="sse", host=_host, port=_port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
