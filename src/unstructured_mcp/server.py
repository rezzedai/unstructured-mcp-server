"""MCP server exposing Unstructured.io document processing tools."""

import json
import logging
import time

from mcp.server.fastmcp import FastMCP

from .chunker import ChunkResult, chunk
from .partitioner import PartitionResult, partition
from .utils import resolve_input

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("unstructured-mcp")

mcp = FastMCP(
    "unstructured",
    instructions=(
        "Document processing with Unstructured.io — partition, chunk, "
        "and extract tables from any document format"
    ),
)


def _serialize_elements(elements: list[dict], format: str) -> str:
    if format == "markdown":
        lines = []
        for el in elements:
            el_type = el.get("type", "")
            text = el.get("text", "")
            meta = el.get("metadata", {})
            page = meta.get("page_number", "")
            page_str = f" (p.{page})" if page else ""

            if el_type == "Title":
                lines.append(f"## {text}{page_str}")
            elif el_type == "Table":
                lines.append(f"\n{text}\n")
            elif el_type == "ListItem":
                lines.append(f"- {text}")
            else:
                lines.append(f"{text}{page_str}")
            lines.append("")
        return "\n".join(lines)
    elif format == "text":
        return "\n\n".join(el.get("text", "") for el in elements)
    else:
        return json.dumps(elements, indent=2, default=str)


@mcp.tool()
async def partition_document(
    file_path: str | None = None,
    url: str | None = None,
    strategy: str = "auto",
    output_format: str = "json",
) -> str:
    """Extract structured elements from any document (PDF, PPTX, HTML, etc.).

    Args:
        file_path: Local path to the document file.
        url: Remote URL to fetch and partition. One of file_path or url
            required.
        strategy: Partitioning strategy — "hi_res" (best quality, slower),
            "fast" (speed), or "auto" (default, auto-detects).
        output_format: Output format — "json" (structured elements),
            "markdown", or "text".

    Returns:
        Extracted document elements with type, text content, and metadata.
    """
    if strategy not in ("hi_res", "fast", "auto"):
        return json.dumps(
            {"error": f"Invalid strategy '{strategy}'. Use: hi_res, fast, auto"}
        )
    if output_format not in ("json", "markdown", "text"):
        return json.dumps(
            {
                "error": (
                    f"Invalid output_format '{output_format}'. "
                    "Use: json, markdown, text"
                )
            }
        )

    start = time.time()
    try:
        input_path = await resolve_input(file_path, url)
        result: PartitionResult = partition(input_path, strategy=strategy)
        elapsed = time.time() - start

        logger.info(
            "Partitioned %s: %d elements, strategy=%s, %.1fs",
            file_path or url,
            len(result.elements),
            result.strategy_used,
            elapsed,
        )

        output = _serialize_elements(result.elements, output_format)

        if output_format == "json":
            return json.dumps(
                {
                    "elements": result.elements,
                    "metadata": {
                        "element_count": len(result.elements),
                        "strategy_used": result.strategy_used,
                        "processing_time_seconds": round(elapsed, 2),
                        "source": file_path or url,
                    },
                },
                indent=2,
                default=str,
            )
        return output
    except FileNotFoundError as e:
        return json.dumps(
            {"error": str(e), "suggestion": "Check that the file path is correct."}
        )
    except Exception as e:
        logger.error("Partition failed: %s", e)
        return json.dumps({"error": str(e)})


@mcp.tool()
async def chunk_document(
    file_path: str | None = None,
    url: str | None = None,
    strategy: str = "auto",
    chunk_strategy: str = "by_title",
    max_characters: int = 1000,
    overlap: int = 200,
) -> str:
    """Partition and chunk a document for RAG pipelines.

    Chunks by semantic boundaries (titles/sections).

    Args:
        file_path: Local path to the document file.
        url: Remote URL to fetch and chunk. One of file_path or url required.
        strategy: Partitioning strategy — "hi_res", "fast", or "auto"
            (default).
        chunk_strategy: Chunking method — "by_title" (semantic, default)
            or "basic" (fixed-size).
        max_characters: Maximum chunk size in characters (default: 1000).
        overlap: Character overlap between chunks (default: 200).

    Returns:
        Array of text chunks with metadata, ready for embedding.
    """
    start = time.time()
    try:
        input_path = await resolve_input(file_path, url)
        result: ChunkResult = chunk(
            input_path,
            strategy=strategy,
            chunk_strategy=chunk_strategy,
            max_characters=max_characters,
            overlap=overlap,
        )
        elapsed = time.time() - start

        logger.info(
            "Chunked %s: %d chunks (from %d elements), %.1fs",
            file_path or url,
            len(result.chunks),
            result.element_count,
            elapsed,
        )

        return json.dumps(
            {
                "chunks": result.chunks,
                "metadata": {
                    "chunk_count": len(result.chunks),
                    "element_count": result.element_count,
                    "chunk_strategy": chunk_strategy,
                    "max_characters": max_characters,
                    "overlap": overlap,
                    "processing_time_seconds": round(elapsed, 2),
                    "source": file_path or url,
                },
            },
            indent=2,
            default=str,
        )
    except Exception as e:
        logger.error("Chunking failed: %s", e)
        return json.dumps({"error": str(e)})


@mcp.tool()
async def extract_tables(
    file_path: str | None = None,
    url: str | None = None,
    output_format: str = "markdown",
) -> str:
    """Extract tables from a document.

    Handles complex table layouts that other parsers break on.

    Args:
        file_path: Local path to the document file.
        url: Remote URL to fetch and extract tables from. One of file_path
            or url required.
        output_format: Table output format — "markdown" (default), "json",
            or "csv".

    Returns:
        Extracted tables with headers, rows, and page location.
    """
    start = time.time()
    try:
        input_path = await resolve_input(file_path, url)
        result: PartitionResult = partition(input_path, strategy="hi_res")

        tables = [el for el in result.elements if el.get("type") == "Table"]

        if not tables:
            return json.dumps(
                {
                    "tables": [],
                    "message": "No tables found in document.",
                    "source": file_path or url,
                }
            )

        elapsed = time.time() - start
        logger.info(
            "Extracted %d tables from %s, %.1fs",
            len(tables),
            file_path or url,
            elapsed,
        )

        formatted_tables = []
        for i, table in enumerate(tables):
            meta = table.get("metadata", {})
            formatted = {
                "index": i,
                "page_number": meta.get("page_number"),
                "text": table.get("text", ""),
            }
            if meta.get("text_as_html"):
                formatted["html"] = meta["text_as_html"]
            formatted_tables.append(formatted)

        if output_format == "csv":
            lines = []
            for t in formatted_tables:
                lines.append(
                    f"--- Table {t['index']} "
                    f"(page {t.get('page_number', '?')}) ---"
                )
                lines.append(t["text"])
                lines.append("")
            return "\n".join(lines)
        elif output_format == "markdown":
            lines = []
            for t in formatted_tables:
                lines.append(
                    f"### Table {t['index'] + 1} "
                    f"(page {t.get('page_number', '?')})"
                )
                lines.append("")
                lines.append(t["text"])
                lines.append("")
            return "\n".join(lines)
        else:
            return json.dumps(
                {
                    "tables": formatted_tables,
                    "metadata": {
                        "table_count": len(formatted_tables),
                        "processing_time_seconds": round(elapsed, 2),
                        "strategy_used": "hi_res",
                        "source": file_path or url,
                    },
                },
                indent=2,
                default=str,
            )
    except Exception as e:
        logger.error("Table extraction failed: %s", e)
        return json.dumps({"error": str(e)})


def main():
    mcp.run()


if __name__ == "__main__":
    main()
