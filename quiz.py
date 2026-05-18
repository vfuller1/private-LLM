"""
quiz.py — Generate and take a multiple-choice quiz on any topic
that's in your indexed documents.

How it works:
  1. You pick a topic (or "random" — picks one from your docs).
  2. We retrieve the most relevant chunks from chroma_db.
  3. We ask the local LLM to write N multiple-choice questions
     grounded ONLY in those chunks, in strict JSON.
  4. You answer each question; we grade you at the end and show
     explanations.

Run with:
    python quiz.py
    python quiz.py --topic "vector search"
    python quiz.py --topic random --n 10
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import textwrap
from dataclasses import dataclass

import chromadb
import ollama

import config


# Topics suggested when the user just runs `python quiz.py` with no topic.
# These match the knowledge docs in docs/, but the script works on any
# corpus you've indexed.
SUGGESTED_TOPICS = [
    "AI governance",
    "Retrieval-Augmented Generation (RAG)",
    "Model Context Protocol (MCP)",
    "embeddings",
    "chunking",
    "agent architecture",
    "vector search",
]


# How many chunks we pull as the LLM's source material per quiz.
QUIZ_CONTEXT_K = 8


SYSTEM_PROMPT = textwrap.dedent("""\
    You are a precise quiz writer. You write multiple-choice questions
    that test understanding of specific facts and concepts from the
    provided context. You NEVER invent information that is not in the
    context.

    Hard rules:
      - Every question must be answerable from the context.
      - Each question has exactly 4 options labeled A, B, C, D.
      - Exactly ONE option is correct.
      - Wrong options are plausible but clearly incorrect from the context.
      - Output VALID JSON ONLY. No markdown fences, no prose, no comments.
""")


USER_PROMPT_TEMPLATE = textwrap.dedent("""\
    Topic: {topic}

    Context (drawn from the user's indexed documents):
    ---
    {context}
    ---

    Write exactly {n} multiple-choice questions about the topic above,
    using only facts present in the context.

    Return STRICT JSON in this exact shape (no other text):

    {{
      "questions": [
        {{
          "question": "string — the question text",
          "options": {{
            "A": "string",
            "B": "string",
            "C": "string",
            "D": "string"
          }},
          "answer": "A" | "B" | "C" | "D",
          "explanation": "string — 1-2 sentences citing the context"
        }}
      ]
    }}
""")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Question:
    text: str
    options: dict[str, str]   # {"A": "...", "B": "...", ...}
    answer: str               # "A" / "B" / "C" / "D"
    explanation: str


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def embed(text: str) -> list[float]:
    return ollama.embeddings(model=config.EMBED_MODEL, prompt=text)["embedding"]


def fetch_context(collection, topic: str, k: int) -> tuple[str, list[str]]:
    """
    Retrieve the top-k chunks for the topic. Returns the joined context
    string plus the list of source filenames for citation.
    """
    q_vec = embed(topic)
    results = collection.query(query_embeddings=[q_vec], n_results=k)
    docs = results["documents"][0]
    metas = results["metadatas"][0]

    sources = sorted({m.get("source", "?") for m in metas})
    context = "\n\n".join(f"[chunk {i + 1}] {d}" for i, d in enumerate(docs))
    return context, sources


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

def strip_code_fences(text: str) -> str:
    """
    Some models wrap JSON in ```json ... ``` even when told not to.
    Strip the fences if present.
    """
    text = text.strip()
    if text.startswith("```"):
        # remove leading ``` and optional language tag
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        if text.endswith("```"):
            text = text[: -3]
    return text.strip()


def extract_json_block(text: str) -> str:
    """
    Pull the first {...} JSON object out of the model's response,
    in case it added prose before or after.
    """
    text = strip_code_fences(text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text  # let json.loads raise the real error
    return text[start : end + 1]


def generate_questions(topic: str, context: str, n: int) -> list[Question]:
    prompt = USER_PROMPT_TEMPLATE.format(topic=topic, context=context, n=n)

    response = ollama.chat(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        format="json",        # ask Ollama to enforce JSON output
        options={"temperature": 0.4},
    )
    raw = response["message"]["content"]
    try:
        data = json.loads(extract_json_block(raw))
    except json.JSONDecodeError as exc:
        print("\nThe model didn't return valid JSON. Raw output:")
        print(raw)
        raise SystemExit(f"\nJSON parse error: {exc}")

    questions: list[Question] = []
    for q in data.get("questions", []):
        try:
            questions.append(
                Question(
                    text=q["question"].strip(),
                    options={k: v.strip() for k, v in q["options"].items()},
                    answer=q["answer"].strip().upper(),
                    explanation=q["explanation"].strip(),
                )
            )
        except (KeyError, AttributeError) as exc:
            print(f"  ! Skipping malformed question: {exc}")
            continue

    return questions


# ---------------------------------------------------------------------------
# Quiz loop
# ---------------------------------------------------------------------------

def ask(question: Question, idx: int, total: int) -> bool:
    """Show one question, read the user's answer, return True if correct."""
    print(f"\nQuestion {idx}/{total}")
    print(question.text)
    for letter in ("A", "B", "C", "D"):
        opt = question.options.get(letter, "")
        print(f"  {letter}. {opt}")

    while True:
        try:
            choice = input("Your answer (A/B/C/D, or 'q' to quit): ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print()
            raise SystemExit(0)

        if choice == "Q":
            raise SystemExit(0)
        if choice in {"A", "B", "C", "D"}:
            break
        print("  Please enter A, B, C, or D.")

    correct = choice == question.answer
    if correct:
        print("  ✓ Correct.")
    else:
        print(f"  ✗ Incorrect. The correct answer is {question.answer}.")
    print(f"  Explanation: {question.explanation}")
    return correct


def print_summary(correct: int, total: int, topic: str, sources: list[str]) -> None:
    pct = (correct / total * 100) if total else 0
    print("\n" + "=" * 50)
    print(f"Quiz complete — Topic: {topic}")
    print(f"Score: {correct}/{total}  ({pct:.0f}%)")
    if pct == 100:
        print("Perfect — you've nailed this topic.")
    elif pct >= 80:
        print("Strong showing. A spot review of the misses and you're set.")
    elif pct >= 60:
        print("Solid foundation. Re-read the source docs and try again.")
    else:
        print("Worth another pass — open the docs/ folder and review.")
    if sources:
        print("Source documents:")
        for s in sources:
            print(f"  - {s}")
    print("=" * 50)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Take an interactive quiz from your indexed docs."
    )
    p.add_argument(
        "--topic",
        default=None,
        help="Topic to quiz on. Use 'random' to pick from suggested topics. "
             "If omitted, you'll be prompted.",
    )
    p.add_argument(
        "--n",
        type=int,
        default=5,
        help="Number of questions (default: 5).",
    )
    return p.parse_args()


def pick_topic_interactively() -> str:
    print("Pick a topic (or type your own):\n")
    for i, t in enumerate(SUGGESTED_TOPICS, start=1):
        print(f"  {i}. {t}")
    print(f"  {len(SUGGESTED_TOPICS) + 1}. Random")
    print(f"  {len(SUGGESTED_TOPICS) + 2}. Type my own topic")

    while True:
        try:
            choice = input("\nChoice: ").strip()
        except (EOFError, KeyboardInterrupt):
            raise SystemExit(0)

        if choice.isdigit():
            n = int(choice)
            if 1 <= n <= len(SUGGESTED_TOPICS):
                return SUGGESTED_TOPICS[n - 1]
            if n == len(SUGGESTED_TOPICS) + 1:
                return random.choice(SUGGESTED_TOPICS)
            if n == len(SUGGESTED_TOPICS) + 2:
                custom = input("Topic: ").strip()
                if custom:
                    return custom
        print("  Please pick a number from the list.")


def main() -> None:
    args = parse_args()

    if not config.DB_DIR.exists():
        print("No vector database found. Run `python ingest.py` first.")
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(config.DB_DIR))
    try:
        collection = client.get_collection(config.COLLECTION_NAME)
    except Exception:
        print("Collection not found. Did `python ingest.py` finish successfully?")
        sys.exit(1)

    topic = args.topic
    if topic is None:
        topic = pick_topic_interactively()
    elif topic.lower() == "random":
        topic = random.choice(SUGGESTED_TOPICS)

    print(f"\nGenerating {args.n} questions on: {topic}")
    print("(retrieving relevant chunks + asking the local LLM — please wait)\n")

    context, sources = fetch_context(collection, topic, QUIZ_CONTEXT_K)
    if not context.strip():
        print("No content found for this topic. Make sure your docs/ contains "
              "material on it and you've run `python ingest.py`.")
        sys.exit(1)

    questions = generate_questions(topic, context, args.n)
    if not questions:
        print("The model couldn't generate questions. Try a different topic "
              "or a more capable model (set LLM_MODEL in config.py).")
        sys.exit(1)

    print(f"Ready — {len(questions)} questions. Type 'q' anytime to quit.")
    print("-" * 50)

    correct = 0
    for idx, q in enumerate(questions, start=1):
        if ask(q, idx, len(questions)):
            correct += 1

    print_summary(correct, len(questions), topic, sources)


if __name__ == "__main__":
    main()
