from splitter import chunk_with_metadata

import pytest


@pytest.fixture
def sample_md_content():
    return (
        "# Header 1\nThis is some content.\n## Header 2\nMore content here on line 4."
    )


@pytest.fixture
def sample_code_content():
    return "def hello():\n    print('world')\n\n# Line 4 code"


def test_metadata_file_path(tmp_path, sample_md_content):
    """Verify the file path is correctly injected into metadata."""
    file = tmp_path / "test.md"
    file.write_text(sample_md_content)

    chunks = chunk_with_metadata(str(file), sample_md_content)

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.metadata["file_path"] == str(file)


def test_line_number_calculation(tmp_path):
    """Check if start_line and end_line are mathematically correct."""
    content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
    file = tmp_path / "test.txt"
    file.write_text(content)

    # Small chunk size to force multiple chunks
    chunks = chunk_with_metadata(str(file), content, chunk_size=10, chunk_overlap=0)

    for chunk in chunks:
        assert "start_line" in chunk.metadata
        assert "end_line" in chunk.metadata
        assert chunk.metadata["start_line"] <= chunk.metadata["end_line"]


def test_code_splitter_logic(tmp_path, sample_code_content):
    """Verify code splitters (Python) handle the syntax correctly."""
    file = tmp_path / "script.py"
    file.write_text(sample_code_content)

    chunks = chunk_with_metadata(
        str(file), sample_code_content, chunk_size=20, chunk_overlap=0
    )

    assert len(chunks) >= 1
    # Check if lines were tracked for the python file
    assert chunks[0].metadata["start_line"] == 1


def test_json_splitter(tmp_path):
    import json

    # Use a slightly larger structure and chunk size
    data = {
        "project": "test",
        "version": 1,
        "description": "a basic test case for json",
    }
    content = json.dumps(data)
    file = tmp_path / "data.json"
    file.write_text(content)

    # Increase chunk_size to ensure it can actually split something
    chunks = chunk_with_metadata(str(file), content, chunk_size=50)

    assert len(chunks) > 0
    assert chunks[0].metadata["file_path"] == str(file)
    # Check that it actually parsed the content
    assert "project" in chunks[0].page_content


def test_unsupported_extension_fallback(tmp_path):
    """Files like .txt should fall back to the default RecursiveCharacterTextSplitter."""
    content = "Plain text content."
    file = tmp_path / "test.txt"
    file.write_text(content)

    chunks = chunk_with_metadata(str(file), content)
    assert len(chunks) == 1
    assert chunks[0].metadata["start_index"] == 0


def test_empty_file(tmp_path):
    """Gracefully handle empty strings."""
    file = tmp_path / "empty.txt"
    file.write_text("")

    chunks = chunk_with_metadata(str(file), "")
    assert chunks == []
