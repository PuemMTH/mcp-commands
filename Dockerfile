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
EXPOSE 8432

# Default: Streamable HTTP transport for containerized use
ENV MCP_TRANSPORT=streamable-http
ENV MCP_PORT=8432

CMD ["uv", "run", "mcp-commands"]
