# AGENTS.md - Guidelines for AI Coding Agents

## Project Overview
FastAPI backend that proxies chat requests to OpenRouter-compatible LLM APIs with streaming SSE responses and optional reasoning output. Includes a modular HTTP client with a pluggable tool system.

## Environment
- **Python**: 3.12+
- **Package manager**: `uv`
- **Virtual env**: `.venv/` (auto-managed by uv)

## Commands

### Run the server
```bash
uv run fastapi dev main.py          # Development with hot reload
uv run fastapi run main.py          # Production mode
```

### Run the client
```bash
uv run python chat_client.py
```

### Add dependencies
```bash
uv add <package>                    # Runtime dependency
uv add --dev <package>              # Dev dependency
```

### Linting & Formatting (install first: `uv add --dev ruff`)
```bash
uv run ruff check .                 # Lint
uv run ruff check --fix .           # Auto-fix
uv run ruff format .                # Format
uv run ruff format --check .        # Check formatting
```

### Type Checking (install first: `uv add --dev mypy`)
```bash
uv run mypy .
```

### Testing (install first: `uv add --dev pytest pytest-asyncio httpx`)
```bash
uv run pytest                       # Run all tests
uv run pytest tests/test_foo.py     # Run single test file
uv run pytest -k test_name          # Run test by name
uv run pytest -v                    # Verbose output
```

## Code Style

### Imports
- Order: stdlib → third-party → local (one blank line between groups)
- Use absolute imports; avoid relative imports
- Import specific types: `from typing import AsyncGenerator, cast`

### Types
- **Always** annotate function signatures (params and return types)
- Use `list[T]` / `dict[K, V]` syntax (Python 3.9+), not `List[T]`
- Use `cast()` when narrowing types from external libraries
- Pydantic `BaseModel` for request/response schemas
- `BaseSettings` from `pydantic-settings` for configuration

### Naming
- `snake_case` for functions, variables, modules
- `PascalCase` for classes, models
- Leading underscore for private/internal functions: `_stream_chunks`

### Formatting
- Follow `ruff` defaults (compatible with Black)
- 4-space indentation, no tabs
- Max line length: 88 (Black default)
- Trailing commas in multi-line structures

### Async Patterns
- Use `async def` for I/O-bound operations
- Prefer `AsyncOpenAI` over sync client for FastAPI endpoints
- Use `AsyncGenerator` for streaming responses
- Stream with `async for` over response iterators

### Error Handling
- Let FastAPI handle validation errors automatically via Pydantic
- Use `response.raise_for_status()` in client code
- Avoid bare `except:` — catch specific exceptions
- Do not expose internal errors or API keys to clients

### Project Structure
```
main.py              # FastAPI application (server)
chat_client.py       # Entry point for the client
pyproject.toml       # Dependencies and project metadata
.env                 # Environment variables (gitignored)

tools/               # Server-side tool infrastructure
  __init__.py
  models.py          # Pydantic schemas for tool definitions
  streaming.py       # SSE event helpers for tool_call events

client/              # Client-side package
  __init__.py
  main.py            # Conversation loop + SSE parsing
  tools/             # Pluggable tool implementations
    __init__.py      # TOOLS + AVAILABLE_TOOLS registry
    weather.py       # Example: get_weather tool
```

### Adding Tools
1. Create `client/tools/<tool_name>.py` with the implementation
2. Register in `client/tools/__init__.py`:
   - Add tool definition to `TOOLS`
   - Add function to `AVAILABLE_TOOLS`

### Conventions
- No comments unless explaining non-obvious logic
- No emojis in code
- Keep functions small and single-purpose
- Use `json.dumps()` for SSE event payloads
- Yield SSE format: `data: {json}\n\n`
