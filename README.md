# mcp-commands

MCP server สำหรับติดตามการใช้งาน AI commands

เก็บข้อมูลว่าใช้ command อะไรบ้าง เมื่อไหร่ และบริบทใดบ้าง โดยใช้ SQLite เป็น storage

## ติดตั้ง

```bash
cd ~/Desktop/mcp_commands
uv sync
```

## โครงสร้าง

```
mcp_commands/
├── src/
│   └── mcp_commands/
│       ├── __init__.py
│       ├── server.py     # MCP server & tools
│       └── storage.py    # SQLite storage layer
├── pyproject.toml
└── README.md
```

**Database:** `~/.local/share/mcp_commands/commands.db`

## MCP Tools

| Tool | คำอธิบาย |
|------|----------|
| `log_command_tool` | บันทึก command ที่ใช้งาน |
| `get_history_tool` | ดูประวัติการใช้งาน |
| `get_stats_tool` | สถิติสรุปการใช้งาน |
| `search_commands_tool` | ค้นหา command ในประวัติ |
| `delete_command_tool` | ลบ record ด้วย id |

## เพิ่มใน Claude Code (~/.claude.json)

```json
{
  "mcpServers": {
    "mcp-commands": {
      "command": "/home/puem/Desktop/mcp_commands/.venv/bin/python",
      "args": ["-m", "mcp_commands.server"],
      "cwd": "/home/puem/Desktop/mcp_commands"
    }
  }
}
```

## ตัวอย่างการใช้งาน

```
log_command_tool(command="/recap",         category="session",  context="morning standup")
log_command_tool(command="/commit",        category="git")
log_command_tool(command="deep-research",  category="research", context="MCP protocol study")

get_history_tool(limit=10)
get_stats_tool()
search_commands_tool(query="git")
```

## Categories แนะนำ

| Category | คำอธิบาย |
|----------|----------|
| `git` | git related commands |
| `session` | session management |
| `research` | research tools |
| `oracle` | oracle commands |
| `code` | coding tools |
