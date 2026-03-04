import json

import pytest

from unstructured_mcp.server import partition_document


@pytest.fixture
def sample_txt(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text(
        "# Meeting Notes\n\nDiscussed Q1 results. Revenue up 15%."
        "\n\n## Action Items\n\n- Follow up with sales team"
        "\n- Prepare board deck"
    )
    return str(f)


async def test_partition_text_file(sample_txt):
    result = await partition_document(file_path=sample_txt, output_format="json")
    data = json.loads(result)
    assert "elements" in data
    assert len(data["elements"]) > 0


async def test_partition_markdown_output(sample_txt):
    result = await partition_document(
        file_path=sample_txt, output_format="markdown"
    )
    assert "Meeting Notes" in result


async def test_partition_text_output(sample_txt):
    result = await partition_document(file_path=sample_txt, output_format="text")
    assert "Meeting Notes" in result
    assert "Revenue up 15%" in result


async def test_partition_invalid_strategy(sample_txt):
    result = await partition_document(file_path=sample_txt, strategy="invalid")
    data = json.loads(result)
    assert "error" in data
