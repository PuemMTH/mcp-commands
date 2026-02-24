# mcp-commands

MCP server สำหรับติดตามการใช้งาน AI commands

เก็บข้อมูลว่าใช้ command อะไรบ้าง เมื่อไหร่ และบริบทใดบ้าง โดยใช้ PostgreSQL เป็น storage

## Architecture

```
Private Server (Docker Compose)
├── mcp-commands-db      ← PostgreSQL 16
└── mcp-commands-server  ← SSE mode, port 8432

Claude Code (ทุก machine)
└── url: "http://your-server:8432/sse"   ← ไม่ต้อง install อะไรเพิ่ม
```

ไม่ต้องแยก server กับ client — codebase เดียวรองรับทั้งสองโหมดผ่าน `MCP_TRANSPORT`

---

## Option A: Central Server (แนะนำ)

### Deploy บน private server

```bash
git clone https://github.com/PuemMTH/mcp-commands
cd mcp-commands
cp .env.example .env          # แก้ POSTGRES_PASSWORD
docker compose up -d
```

### เพิ่มใน Claude Code (~/.claude.json) — ทุก machine

```json
{
  "mcpServers": {
    "mcp-commands": {
      "url": "http://your-server:8432/sse"
    }
  }
}
```

ข้อมูลทุก session เก็บรวมใน Postgres เดียวกัน

---

## Option B: รัน Local ด้วย uvx

สำหรับคนที่อยากรัน instance ของตัวเองแบบ stdio (ต้องมี PostgreSQL อยู่แล้ว)

```bash
# ตั้ง DATABASE_URL ให้ชี้ไป Postgres ของตัวเอง
DATABASE_URL=postgresql://user:pass@localhost:5432/mcp_commands \
  uvx --from git+https://github.com/PuemMTH/mcp-commands mcp-commands
```

เพิ่มใน Claude Code (~/.claude.json):

```json
{
  "mcpServers": {
    "mcp-commands": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/PuemMTH/mcp-commands", "mcp-commands"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/mcp_commands"
      }
    }
  }
}
```

---

## MCP Tools

| Tool | คำอธิบาย |
|------|----------|
| `log_command_tool` | บันทึก command ที่ใช้งาน |
| `get_history_tool` | ดูประวัติการใช้งาน |
| `get_stats_tool` | สถิติสรุปการใช้งาน |
| `search_commands_tool` | ค้นหา command ในประวัติ |
| `delete_command_tool` | ลบ record ด้วย id |

## ตัวอย่างการใช้งาน

```
log_command_tool(command="/recap",         category="session",  context="morning standup")
log_command_tool(command="/commit",        category="git")
log_command_tool(command="deep-research",  category="research", context="MCP protocol study")

get_history_tool(limit=10)
get_stats_tool()
search_commands_tool(query="git")
```

## Environment Variables

| Variable | Default | คำอธิบาย |
|----------|---------|----------|
| `DATABASE_URL` | `postgresql://mcp_commands:mcp_commands@localhost:5432/mcp_commands` | PostgreSQL DSN |
| `MCP_TRANSPORT` | `stdio` | `stdio` หรือ `sse` |
| `MCP_PORT` | `8432` | Port สำหรับ SSE mode |

## Categories แนะนำ

| Category | คำอธิบาย |
|----------|----------|
| `git` | git related commands |
| `session` | session management |
| `research` | research tools |
| `oracle` | oracle commands |
| `code` | coding tools |
| `skill` | Claude Code skills |
