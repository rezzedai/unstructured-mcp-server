"""Tests for partition_document tool."""

import json
import os
import pytest

from unstructured_mcp.server import partition_document


@pytest.fixture
def sample_txt(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("# Meeting Notes\n\nDiscussed Q1 results. Revenue up 15%.\n\n## Action Items\n\n- Follow up with sales team\n- Prepare board deck")
    return str(f)


async def test_partition_text_file(sample_txt):
    result = await partition_document(file_path=sample_txt, output_format="json")
    data = json.loads(result)
    assert "elements" in data
    assert data["metadata"]["element_count"] > 0
    assert data["metadata"]["strategy_used"] in ("fast", "auto", "hi_res")


async def test_partition_markdown_output(sample_txt):
    result = await partition_document(file_path=sample_txt, output_format="markdown")
    assert isinstance(result, str)
    assert len(result) > 0


async def test_partition_text_output(sample_txt):
    result = await partition_document(file_path=sample_txt, output_format="text")
    assert isinstance(result, str)
    assert "Meeting" in result or "Revenue" in result or "Action" in result


async def test_partition_missing_file():
    result = await partition_document(file_path="/nonexistent/file.pdf")
    data = json.loads(result)
    assert "error" in data
    assert "suggestion" in data


async def test_partition_invalid_strategy(sample_txt):
    result = await partition_document(file_path=sample_txt, strategy="invalid")
    data = json.loads(result)
    assert "error" in data


async def test_partition_no_input():
    result = await partition_document()
    data = json.loads(result)
    assert "error" in data
