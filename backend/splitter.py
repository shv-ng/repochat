import json
import pprint
from pathlib import Path

from langchain_text_splitters import (HTMLSectionSplitter, Language,
                                      MarkdownHeaderTextSplitter,
                                      RecursiveCharacterTextSplitter,
                                      RecursiveJsonSplitter)

EXTENSION_MAP = {
    ".py": Language.PYTHON,
    ".cpp": Language.CPP,
    ".go": Language.GO,
    ".java": Language.JAVA,
    ".kt": Language.KOTLIN,
    ".php": Language.PHP,
    ".proto": Language.PROTO,
    ".r": Language.R,
    ".rst": Language.RST,
    ".rb": Language.RUBY,
    ".rs": Language.RUST,
    ".scala": Language.SCALA,
    ".swift": Language.SWIFT,
    ".tex": Language.LATEX,
    ".sol": Language.SOL,
    ".cs": Language.CSHARP,
    ".pl": Language.PERL,
}


def get_splitter(
    ext: str, chunk_size=1000, chunk_overlap=200
) -> (
    RecursiveCharacterTextSplitter
    | MarkdownHeaderTextSplitter
    | RecursiveJsonSplitter
    | HTMLSectionSplitter
):
    """Return the appropriate text splitter based on the file extension.

    Args:
        ext (str): file extension
        chunk_size (int, optional): chunk size. Defaults to 1000.
        chunk_overlap (int, optional): chunk overlap. Defaults to 200.

    Returns:
        RecursiveCharacterTextSplitter | MarkdownHeaderTextSplitter | \
            RecursiveJsonSplitter | HTMLSectionSplitter: text splitter
    """
    if ext in EXTENSION_MAP:
        return RecursiveCharacterTextSplitter.from_language(
            EXTENSION_MAP[ext],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
        )

    match ext:
        case ".md":
            headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]
            return MarkdownHeaderTextSplitter(headers_to_split_on)
        case ".json":
            return RecursiveJsonSplitter(max_chunk_size=chunk_size)
        case ".html":
            headers_to_split_on = [
                ("<h1>", "Header 1"),
                ("<h2>", "Header 2"),
                ("<h3>", "Header 3"),
            ]
            return HTMLSectionSplitter(
                headers_to_split_on,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                add_start_index=True,
            )
        case _:
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap, add_start_index=True
            )


def chunk_with_metadata(file_path, text, chunk_size=1000, chunk_overlap=200):
    ext = Path(file_path).suffix
    splitter = get_splitter(ext, chunk_size, chunk_overlap)

    initial_metadata = {"file_path": file_path}

    if ext in (".md", ".mdx"):
        chunks = splitter.split_text(text)
        for chunk in chunks:
            chunk.metadata["file_path"] = file_path
        return chunks

    if ext == ".json":
        data = json.loads(text)
        chunks = splitter.create_documents(texts=[data], metadatas=[initial_metadata])
        return chunks

    chunks = splitter.create_documents([text], metadatas=[initial_metadata])

    for chunk in chunks:
        start_char = chunk.metadata.get("start_index", 0)
        end_char = start_char + len(chunk.page_content)

        chunk.metadata["start_line"] = text.count("\n", 0, start_char) + 1
        chunk.metadata["end_line"] = text.count("\n", 0, end_char) + 1

    return chunks


if __name__ == "__main__":
    pprint.pprint(
        chunk_with_metadata(
            "./main.py",
            Path("./main.py").read_text(),
        )
    )
