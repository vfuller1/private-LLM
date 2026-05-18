"""
Settings for Ask My Docs. Edit these values to experiment.

Everything in this file is just a knob you can turn. Once you've got the
project running, come back here and try different values to see how the
behavior changes.
"""

from pathlib import Path

# --- Models (must match what you pulled with `ollama pull ...`) ---

# The LLM that actually writes answers.
# Smaller = faster but less smart. Bigger = slower but better.
#
# Recommended for your machine (RTX 5060 Ti 8 GB + 32 GB RAM):
#   "llama3.1:8b"   ~5 GB   — fits entirely in VRAM, fast and capable  ← default
#   "qwen2.5:7b"    ~4 GB   — strong alternative, great at reasoning
#   "mistral"       ~4 GB   — solid Mistral 7B, good general-purpose
#   "qwen2.5:14b"   ~9 GB   — smarter, mixes VRAM + system RAM, a bit slower
#   "phi4"          ~9 GB   — Microsoft's 14B, very capable for its size
#   "llama3.2:3b"   ~2 GB   — fastest, fall back here if anything feels sluggish
LLM_MODEL = "llama3.1:8b"

# The embedding model — turns text into vectors so we can search by meaning.
# nomic-embed-text is small, fast, and very good for English documents.
EMBED_MODEL = "nomic-embed-text"


# --- Folders ---

PROJECT_DIR = Path(__file__).parent
DOCS_DIR = PROJECT_DIR / "docs"          # put your PDFs and .txt files here
DB_DIR = PROJECT_DIR / "chroma_db"       # local vector database lives here

# Name of the collection inside Chroma (you can have multiple if you want).
COLLECTION_NAME = "ask_my_docs"


# --- Chunking ---

# Documents are split into overlapping chunks before being embedded.
# Roughly 500 characters ≈ 100 words — small enough to be specific,
# big enough to contain a complete thought.
CHUNK_SIZE = 500       # c