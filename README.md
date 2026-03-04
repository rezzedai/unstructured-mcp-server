# Unstructured MCP Server

[![CI](https://github.com/rezzedai/unstructured-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/rezzedai/unstructured-mcp-server/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An [MCP](https://modelcontextprotocol.io/) server that gives AI agents the ability to read and 
process complex documents using [Unstructured.io](https://unstructured.io/). Extract structured 
content from PDFs, PowerPoints, HTML, images, and more — including tables that other parsers 
break on.

## Features

- **`partition_document`** — Extract structured elements from any document format (PDF, PPTX, 
  DOCX, HTML, images, etc.)
- **`chunk_document`** — Partition and chunk documents for RAG pipelines with semantic boundary 
  detection
- **`extract_tables`** — Focused table extraction with markdown, JSON, or CSV output
- **Dual mode** — Works locally (no API key needed) or with the Unstructured hosted API for 
  production workloads
- **Smart strategy selection** — Auto-detects when high-resolution processing is needed (scanned 
  docs, images) vs. fast mode

## Why This Exists

Document processing is table stakes for AI agents — but most tools treat it as an afterthought. 
PDFs get dumped as raw text, tables lose their structure, and scanned documents are ignored 
entirely.

This server bridges that gap by exposing Unstructured's document intelligence as MCP tools that 
any AI agent can call natively. No custom integration code, no preprocessing scripts — just wire 
it up and ask your agent to read a document.

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   AI Agent      │────▶│  MCP Server          │────▶│  Unstructured SDK   │
│   (Claude, etc) │◀────│  (FastMCP)           │◀────│  or Hosted API      │
│                 │     │                      │     │                     │
│  "Read this PDF"│     │  partition_document  │     │  OCR, layout        │
│                 │     │  chunk_document      │     │  analysis, table    │
│                 │     │  extract_tables      │     │  detection          │
└─────────────────┘     └──────────────────────┘     └─────────────────────┘
```

The server is a thin, focused layer — it doesn't try to be smart about documents. It delegates 
that entirely to Unstructured's SDK, which has years of investment in layout analysis, OCR, and 
table detection. The MCP layer handles input resolution (local files or URLs), output formatting, 
and strategy selection.

## Quick Start

### Install

```bash
pip install unstructured-mcp-server
```

Or from source:

```bash
git clone https://github.com/rezzedai/unstructured-mcp-server
cd unstructured-mcp-server
pip install -e .
```

For offline environments, pre-download the required spaCy model:

```bash
python -m spacy download en_core_web_sm
```

### Configure

Add to your Claude Code MCP config (`~/.claude.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "unstructured": {
      "command": "python3",
      "args": ["-m", "unstructured_mcp.server"]
    }
  }
}
```

For the hosted API (better OCR, complex layouts):

```json
{
  "mcpServers": {
    "unstructured": {
      "command": "python3",
      "args": ["-m", "unstructured_mcp.server"],
      "env": {
        "UNSTRUCTURED_API_KEY": "your-api-key",
        "UNSTRUCTURED_API_URL": "https://api.unstructuredapp.io/general/v0/general"
      }
    }
  }
}
```

### Use

Once configured, Claude can process documents in any conversation:

> "Read this PDF and give me a summary"
> "Extract all tables from this financial report"
> "Chunk this document for my RAG pipeline"

## Tools

### `partition_document`

Extract structured elements from any document.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | string | — | Local path to document |
| `url` | string | — | Remote URL to fetch |
| `strategy` | string | `auto` | `hi_res`, `fast`, or `auto` |
| `output_format` | string | `json` | `json`, `markdown`, or `text` |

Returns elements with type (Title, NarrativeText, Table, ListItem, etc.), text, and metadata 
(page number, coordinates).

### `chunk_document`

Partition and chunk for RAG. Splits on semantic boundaries (section titles).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | string | — | Local path to document |
| `url` | string | — | Remote URL to fetch |
| `strategy` | string | `auto` | Partition strategy |
| `chunk_strategy` | string | `by_title` | `by_title` (semantic) or `basic` (fixed-size) |
| `max_characters` | int | `1000` | Max chunk size |
| `overlap` | int | `200` | Character overlap between chunks |

### `extract_tables`

Focused table extraction — handles complex layouts, merged cells, nested tables.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | string | — | Local path to document |
| `url` | string | — | Remote URL to fetch |
| `output_format` | string | `markdown` | `markdown`, `json`, or `csv` |

## How It Works

The server wraps the Unstructured SDK with two processing modes:

**Local mode** (default) — Uses the `unstructured` Python package directly. No API key needed. 
Good for development, privacy-sensitive documents, and offline use.

**API mode** — When `UNSTRUCTURED_API_KEY` is set, routes processing through Unstructured's 
hosted service. Better OCR, more robust handling of complex layouts, and support for the full 
range of document types.

The server auto-detects: if the API key is set, it uses the API. Otherwise, it processes locally.

### Strategy Selection

- **`auto`** (default) — Inspects the file and picks the best strategy. Images and large PDFs 
  get `hi_res`; everything else gets `fast`.
- **`hi_res`** — Best quality. Uses OCR for scanned docs, handles complex tables and layouts. 
  Slower.
- **`fast`** — Speed-optimized. Great for digital-native PDFs and text-heavy documents.

## Supported Formats

PDF, DOCX, PPTX, XLSX, HTML, XML, TXT, CSV, TSV, RTF, EML, MSG, PNG, JPG, TIFF, BMP, EPUB, ODT, 
RST, MD

## Development

```bash
git clone https://github.com/rezzedai/unstructured-mcp-server
cd unstructured-mcp-server
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check src/ tests/
```

### Running the server

```bash
# Start in stdio mode (default for MCP)
python -m unstructured_mcp.server

# Or use the installed entry point
unstructured-mcp-server
```

## Docker

```bash
docker build -t unstructured-mcp .
docker run -p 8080:8080 unstructured-mcp
```

## License

MIT
