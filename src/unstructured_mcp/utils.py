"""File handling and format utilities."""

import os
import tempfile
from enum import Enum

import httpx


class OutputFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    TEXT = "text"
    CSV = "csv"


async def resolve_input(file_path: str | None, url: str | None) -> str:
    """Resolve file_path or url to a local file path. Downloads URL if needed."""
    if not file_path and not url:
        raise ValueError("Either file_path or url is required.")

    if file_path:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path

    # Download URL to temp file
    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        response = await client.get(url)
        response.raise_for_status()

    # Detect extension from URL or content-type
    ext = _detect_extension(url, response.headers.get("content-type", ""))

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(response.content)
    tmp.close()

    return tmp.name


def _detect_extension(url: str, content_type: str) -> str:
    """Detect file extension from URL or content-type."""
    # Try URL first
    path = url.split("?")[0]
    if "." in path.split("/")[-1]:
        ext = "." + path.split("/")[-1].rsplit(".", 1)[1]
        if len(ext) <= 5:
            return ext

    # Fall back to content-type
    ct_map = {
        "application/pdf": ".pdf",
        "text/html": ".html",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "text/plain": ".txt",
    }

    for ct, ext in ct_map.items():
        if ct in content_type:
            return ext

    return ".bin"
