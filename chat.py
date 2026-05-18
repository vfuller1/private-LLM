"""
chat.py — A simple CLI chat loop that answers questions using the
chunks you indexed with ingest.py.

For each question we:
  1. Embed the question with the same model used during ingest.
  2. Ask Chroma for the TOP_K nearest chunks.
  3. Stuff those chunks into a prompt template along with the question.
  4. Stream the local LLM's answer back to the terminal.
  5. Print the source files we drew from.

Run with:

    python chat.py
"""

from __future__ import annotations

import sys
import textwrap

import chromadb
import ollama

import config


SYSTEM_PROMPT = textwrap.dedent("""\
    You are a helpful assistant that answers questions using ONLY the
    provided context. If the answer isn't in the context, say
    "I don't know based on the provided documents." Be concise and
    cite specific facts from the context when possible.
""")


PROMPT_TEMPLATE = textwrap.dedent("""\
    Context from the user's documents:
    ---
    {context}
    ---

    Question: {question}

    Answer using only the context above.
""")


def embed_question(text: str) -> list[float]:
    """Same embedding call as in ingest.py — must use the same model."""
    response = ollama.embeddings(model=config.EMBED_MODEL, prompt=text)
    return response["embedding"]


def retrieve(collection, question: str, k: int) -> tuple[list[str], list[dict]]:
    """Find the top-k chunks whose embeddings are nearest to the question."""
    q_vec = embed_question(question)
    results = collection.query(query_embeddings=[q_vec], n_results=k)
    # Chroma returns lists-of-lists because you can ask multiple queries at once.
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    return docs, metas


def build_prompt(question: str, chunks: list[str]) -> str:
    context = "\n\n".join(f"[chunk {i + 1}] {c}" for i, c in enumerate(chunks))
    return PROMPT_TEMPLATE.format(context=context, question=question)


def stream_answer(prompt: str) -> str:
    """
    Send the prompt to the local LLM and stream tokens to stdout as they arrive.
    Returns the full answer text once streaming completes.
    """
    pieces: list[str] = []
    stream = ollama.chat(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )
    for part in stream:
        token = part.get("message", {}).get("content", "")
        if token:
            print(token, end="", flush=True)
            pieces.append(token)
    print()  # final newline
    return "".join(pieces)


def main() -> None:
    if not config.DB_DIR.exists():
        print("No vector database found. Run `python ingest.py` first.")
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(config.DB_DIR))
    try:
        collection = client.get_collection(config.COLLECTION_NAME)
    except Exception:
        print("Collection not found. Did `python ingest.py` finish successfully?")
        sys.exit(1)

    print(f"Ask My Docs (model: {config.LLM_MODEL}) — type 'quit' to exit.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue
        if question.lower() in {"quit", "exit", "q"}:
            break

        try:
            chunks, metas = retrieve(collection, question, config.TOP_K)
        except Exception as exc:
            print(f"[retrieval error: {exc}]")
            continue

        if not chunks:
            print("Assistant: I don't have any documents indexed yet.\n")
            continue

        prompt = build_prompt(question, chunks)
        print("Assistant: ", end="", flush=True)
        try:
            stream_answer(prompt)
        except Exception as exc:
            print(f"\n[LLM error: {exc}]")
            print("Is Ollama running? Try: `ollama serve` or open the Ollama app.\n")
            continue

        print("Sources:")
        seen = set()
        for meta in metas:
            tag = f"  - {meta.get('source', '?')} (chunk {meta.get('chunk', '?')})"
            if tag not in seen:
                print(tag)
                seen.add(tag)
        print()


if __name__ == "__main__":
    main()
