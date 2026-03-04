"""Tests for extract_tables tool."""

import json

import pytest

from unstructured_mcp.server import extract_tables


@pytest.fixture
def no_table_txt(tmp_path):
    f = tmp_path / "no_tables.txt"
    f.write_text("This is a simple document with no tables whatsoever.")
    return str(f)


async def test_extract_tables_no_tables(no_table_txt):
    result = await extract_tables(file_path=no_table_txt)
    # Could be JSON or markdown depending on output
    if result.startswith("{"):
        data = json.loads(result)
        assert data["tables"] == []
        assert "No tables found" in data.get("message", "")


async def test_extract_tables_missing_file():
    result = await extract_tables(file_path="/nonexistent/file.pdf")
    data = json.loads(result)
    assert "error" in data


async def test_extract_tables_no_input():
    result = await extract_tables()
    data = json.loads(result)
    assert "error" in data
