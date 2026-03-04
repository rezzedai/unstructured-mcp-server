# Contributing

Thanks for your interest in contributing to the Unstructured MCP Server.

## Setup

```bash
git clone https://github.com/rezzedai/unstructured-mcp-server
cd unstructured-mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
```

## Development

```bash
# Run tests
pytest -v

# Lint
ruff check src/ tests/

# Auto-fix lint issues
ruff check --fix src/ tests/
```

## Pull Requests

- Branch from `main`
- Include tests for new functionality
- Ensure `ruff check` and `pytest` pass
- Keep PRs focused — one feature or fix per PR

## Adding Tools

New MCP tools go in `src/unstructured_mcp/server.py`. Follow the pattern of existing tools:

1. Define the async function with `@mcp.tool()`
2. Accept `file_path` and/or `url` parameters
3. Use `resolve_input()` to normalize input
4. Return JSON string with results and metadata

## Code Style

- Python 3.10+ (use `X | Y` union syntax, not `Optional`)
- Ruff for linting (config in `pyproject.toml`)
- Type hints on function signatures
- Docstrings on public functions (Google style)
