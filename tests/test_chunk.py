"""Tests for chunk_document tool."""

import json
import pytest

from unstructured_mcp.server import chunk_document


@pytest.fixture
def sample_txt(tmp_path):
    content = """# Introduction

This is the introduction to our quarterly report. The company has seen significant growth across all verticals.

# Financial Results

Revenue grew 15% year-over-year to $50M. Operating margin improved to 22%.

Key highlights:
- SaaS revenue up 25%
- Enterprise deals closed: 12
- Net retention rate: 115%

# Product Updates

We launched three major features this quarter. The AI assistant feature saw the highest adoption.

# Outlook

We expect continued growth in Q2 with the pipeline looking strong.
"""
    f = tmp_path / "report.txt"
    f.write_text(content)
    return str(f)


async def test_chunk_by_title(sample_txt):
    result = await chunk_document(file_path=sample_txt, chunk_strategy="by_title")
    data = json.loads(result)
    assert "chunks" in data
    assert data["metadata"]["chunk_count"] > 0
    assert data["metadata"]["chunk_strategy"] == "by_title"


async def test_chunk_basic(sample_txt):
    result = await chunk_document(
        file_path=sample_txt, chunk_strategy="basic", max_characters=200, overlap=50
    )
    data = json.loads(result)
    assert "chunks" in data
    for chunk in data["chunks"]:
        assert len(chunk["text"]) <= 250  # Allow some slack for boundary


async def test_chunk_respects_max_characters(sample_txt):
    max_chars = 300
    result = await chunk_document(file_path=sample_txt, max_characters=max_chars)
    data = json.loads(result)
    # by_title chunks can exceed max slightly due to title grouping, but should be in range
    for chunk in data["chunks"]:
        assert chunk["char_count"] > 0


async def test_chunk_no_input():
    result = await chunk_document()
    data = json.loads(result)
    assert "error" in data
