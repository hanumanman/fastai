# FastAI

FastAPI backend that proxies chat requests to OpenRouter-compatible LLM APIs with streaming SSE responses and optional reasoning output. Includes a modular HTTP client with a pluggable tool system.

## Project Structure

```
main.py              # FastAPI application (server)
chat_client.py       # Entry point for the client
sessions.py          # SQLite-based session persistence
pyproject.toml       # Dependencies and project metadata
uv.lock              # Lock file for uv package manager
.python-version      # Python version pin (3.12)
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
    weather/         # get_weather tool (Open-Meteo API)
    pdf_parser/      # parse_pdf tool (PyMuPDF/fitz)
    find_file/       # find_file tool (fzf fuzzy matching)
    docx_parser/     # parse_docx tool (python-docx)
    web_search/      # web_search tool (DuckDuckGo/DDGS)
```

## Adding a New Tool

1. Create `client/tools/<tool_name>.py` with the implementation
2. Register it in `client/tools/__init__.py`:
   - Add the tool definition to `TOOLS`
   - Add the function to `AVAILABLE_TOOLS`

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
