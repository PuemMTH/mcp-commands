FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (for layer caching)
COPY pyproject.toml uv.lock README.md ./

# Copy source code
COPY src/ ./src/

# Install dependencies (no dev, frozen from lock file)
RUN uv sync --frozen --no-dev

# Expose SSE port
EXPOSE 8000

# Default: SSE transport for containerized use
ENV MCP_TRANSPORT=sse
ENV MCP_PORT=8000

CMD ["uv", "run", "mcp-commands"]
