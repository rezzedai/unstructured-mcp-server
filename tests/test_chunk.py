import json

import pytest

from unstructured_mcp.server import chunk_document


@pytest.fixture
def sample_txt(tmp_path):
    content = """# Introduction

This is the introduction to our quarterly report. The company has seen
significant growth across all verticals.

# Financial Results

Revenue grew 15% year-over-year to $50M. Operating margin improved to 22%.

Key highlights:
- Strong enterprise adoption
- International expansion successful
- Product-market fit validated

# Next Steps

We will focus on scaling our sales team and expanding into new markets.
"""
    f = tmp_path / "sample.txt"
    f.write_text(content)
    return str(f)


async def test_chunk_by_title(sample_txt):
    result = await chunk_document(
        file_path=sample_txt, chunk_strategy="by_title", max_characters=500
    )
    data = json.loads(result)
    assert "chunks" in data
    assert len(data["chunks"]) > 0
    assert data["metadata"]["chunk_strategy"] == "by_title"


async def test_chunk_basic(sample_txt):
    result = await chunk_document(
        file_path=sample_txt, chunk_strategy="basic", max_characters=200
    )
    data = json.loads(result)
    assert "chunks" in data
    assert len(data["chunks"]) > 0


async def test_chunk_with_overlap(sample_txt):
    result = await chunk_document(
        file_path=sample_txt,
        chunk_strategy="by_title",
        max_characters=300,
        overlap=50,
    )
    data = json.loads(result)
    assert data["metadata"]["overlap"] == 50
