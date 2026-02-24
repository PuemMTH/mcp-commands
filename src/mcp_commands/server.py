"""
MCP Commands Server
Tracks AI command usage via MCP tools.
"""

import json
import os
from mcp.server.fastmcp import FastMCP
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
    host=_host,
    port=_port,
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
# Entry point
# ─────────────────────────────────────────────

def main():
    mcp.run(transport=_transport)


if __name__ == "__main__":
    main()
