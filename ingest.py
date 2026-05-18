"""
ingest.py — Read documents from docs/, chunk them, embed each chunk
with a local model, and store the embeddings in a local Chroma database.

Run this whenever you add or change files in docs/:

    python ingest.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import chromadb
import ollama
from pypdf import PdfReader

import config


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def load_text_file(path: Path) -> str:
    """Read a plain-text file."""
    return path.read_text(encoding="utf-8", errors="ignore")


def load_pdf(path: Path) -> str:
    """Extract text from every page of a PDF."""
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def load_document(path: Path) -> str:
    """Dispatch to the right loader based on file extension."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix in {".txt", ".md"}:
        return load_text_file(path)
    raise ValueError(f"Unsupported file type: {suffix}")


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """
    Split text into overlapping chunks of roughly `size` characters.

    We use a simple sliding window. Real-world systems often split on
    sentence or paragraph boundaries for better results, but this is
    plenty for a first project.
    """
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    step = max(1, size - overlap)

    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start += step

    return chunks


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

def embed_one(text: str) -> list[float]:
    """
    Ask Ollama to turn a string into a vector using the embedding model.
    The vector is a list of floats representing the text's meaning.
    """
    response = ollama.embeddings(model=config.EMBED_MODEL, prompt=text)
    return response["embedding"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    docs_dir: Path = config.DOCS_DIR
    if not docs_dir.exists():
        print(f"No docs folder found at {docs_dir}.")
        print("Create it and drop some .pdf/.txt files inside, then re-run.")
        sys.exit(1)

    # Connect to (or create) a persistent Chroma DB stored as files on disk.
    client = chromadb.PersistentClient(path=str(config.DB_DIR))

    # Start fresh each time so we don't accumulate stale chunks.
    # For a real app you'd diff and only update what changed.
    try:
        client.delete_collection(config.COLLECTION_NAME)
    except Exception:
        pass  # collection didn't exist yet — fine
    collection = client.create_collection(config.COLLECTION_NAME)

    files = sorted(
        p for p in docs_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".pdf", ".txt", ".md"}
    )
    if not files:
        print(f"No supported files in {docs_dir}. Add .pdf, .txt, or .md files.")
        sys.exit(1)

    print(f"Loading documents from {docs_dir}/")

    all_ids: list[str] = []
    all_documents: list[str] = []
    all_metadatas: list[dict] = []

    for path in files:
        try:
            raw_text = load_document(path)
        except Exception as exc:
            print(f"  ! Skipping {path.name}: {exc}")
            continue

        chunks = chunk_text(raw_text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        print(f"  - {path.name}  ({len(chunks)} chunks)")

        for i, chunk in enumerate(chunks):
            all_ids.append(f"{path.name}::chunk-{i}")
            all_documents.append(chunk)
            all_metadatas.append({"source": path.name, "chunk": i})

    if not all_documents:
        print("Nothing to embed — exiting.")
        sys.exit(1)

    print(f"Embedding {len(all_documents)} chunks with {config.EMBED_MODEL}...")

    # Embed one at a time. Ollama's API doesn't batch, but this is plenty
    # fast for a personal knowledge base.
    embeddings: list[list[float]] = []
    for idx, chunk in enumerate(all_documents, start=1):
        embeddings.append(embed_one(chunk))
        if idx % 10 == 0 or idx == len(all_documents):
            print(f"  {idx}/{len(all_documents)} embedded")

    collection.add(
        ids=all_ids,
        documents=all_documents,
        metadatas=all_metadatas,
        embeddings=embeddings,
    )

    print(f"Done. Stored {len(all_documents)} chunks in {config.DB_DIR}/")
    print("Next step: run `python chat.py`")


if __name__ == "__main__":
    main()
