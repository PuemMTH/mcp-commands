#!/home/puem/Desktop/mcp_commands/.venv/bin/python
"""
Claude Code Hook Logger
Auto-logs every tool invocation to mcp_commands SQLite DB.

Hooked via ~/.claude/settings.json PostToolUse
Receives JSON via stdin from Claude Code.
"""

import sys
import json
from pathlib import Path

# Add src to path so we can import mcp_commands without installing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_commands.storage import log_command


# ─────────────────────────────────────────────
# Category mapping
# ─────────────────────────────────────────────

TOOL_CATEGORY = {
    "Skill":        "skill",
    "Bash":         "bash",
    "Task":         "task",
    "Read":         "file",
    "Write":        "file",
    "Edit":         "file",
    "Glob":         "file",
    "Grep":         "search",
    "WebFetch":     "web",
    "WebSearch":    "web",
    "TodoWrite":    "todo",
    "NotebookEdit": "file",
}


def extract_info(hook_data: dict) -> tuple[str, str, str]:
    """
    Returns (command, category, context) from hook_data.
    """
    tool_name  = hook_data.get("tool_name", "unknown")
    tool_input = hook_data.get("tool_input", {})
    category   = TOOL_CATEGORY.get(tool_name, "tool")

    # ── Skill (slash commands) ──────────────────
    if tool_name == "Skill":
        skill = tool_input.get("skill", "unknown")
        args  = tool_input.get("args", "")
        command = f"/{skill}"
        context = args[:200] if args else ""

    # ── Bash ────────────────────────────────────
    elif tool_name == "Bash":
        cmd  = tool_input.get("command", "")
        desc = tool_input.get("description", "")
        # ใช้ description ถ้ามี ไม่งั้นใช้ command (trim)
        command = cmd[:120].strip()
        context = desc[:200] if desc else ""

    # ── Task (subagent) ─────────────────────────
    elif tool_name == "Task":
        subagent = tool_input.get("subagent_type", "unknown")
        desc     = tool_input.get("description", "")
        command  = f"Task({subagent})"
        context  = desc[:200]

    # ── File tools ──────────────────────────────
    elif tool_name in ("Read", "Write", "Edit", "NotebookEdit"):
        path    = tool_input.get("file_path", tool_input.get("notebook_path", ""))
        command = f"{tool_name}:{Path(path).name}" if path else tool_name
        context = path[:200]

    elif tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        command = f"Glob:{pattern}"
        context = ""

    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        command = f"Grep:{pattern[:60]}"
        context = tool_input.get("path", "")[:200]

    # ── Web ─────────────────────────────────────
    elif tool_name in ("WebFetch", "WebSearch"):
        url_or_query = tool_input.get("url", tool_input.get("query", ""))
        command  = f"{tool_name}:{url_or_query[:80]}"
        context  = ""

    # ── Fallback ─────────────────────────────────
    else:
        command = tool_name
        context = str(tool_input)[:200]

    return command, category, context


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        hook_data = json.loads(raw)
        command, category, context = extract_info(hook_data)

        log_command(
            command=command,
            category=category,
            context=context,
            extra={
                "session_id": hook_data.get("session_id", ""),
                "hook_event": hook_data.get("hook_event_name", ""),
            },
        )
    except Exception:
        # Never block Claude Code — silently ignore errors
        sys.exit(0)


if __name__ == "__main__":
    main()
