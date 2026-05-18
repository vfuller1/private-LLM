# Ask My Docs — Your First Private LLM Project

A 100% local "chat with your documents" app. No data ever leaves your computer —
the language model, the embeddings, and the vector database all run on your machine.

## What you'll build

A small Python program that:

1. Reads PDFs, Word `.docx`, and text files from a `docs/` folder.
2. Splits them into chunks and converts each chunk into a numerical "embedding"
   using a local model.
3. Stores those embeddings in a local vector database (Chroma — just files on disk).
4. When you ask a question, finds the most relevant chunks and feeds them to a
   local LLM (via Ollama), which answers using only that context.
5. Includes a built-in quiz mode that generates multiple-choice tests on the
   topics in your indexed documents — useful for studying.

This pattern is called **RAG** (Retrieval-Augmented Generation) and is the most
common way enterprises put LLMs to work on their own data.

```
You ───▶ question
            │
            ▼
      [embed question]  ──▶ [vector DB] ──▶ top-K relevant chunks
                                                     │
                                                     ▼
                                   [local LLM] ──▶ answer + sources
```

## Prerequisites

- **A computer running macOS, Windows, or Linux**
- **Python 3.10 or newer** — check with `python --version` or `python3 --version`
- **About 5 GB of free disk space** for the LLM and embedding model

GPU is nice but not required. On CPU-only machines, the 3B model below works fine.

## Step 1 — Install Ollama

Ollama is the tool that runs the LLM locally. It handles downloads, GPU detection,
and serves the model on `http://localhost:11434`.

Download and install from **https://ollama.com/download** — there are one-click
installers for macOS, Windows, and Linux.

After installing, open a terminal and verify it works:

```bash
ollama --version
```

## Step 2 — Pull the models

Open PowerShell (or Windows Terminal) and run:

```powershell
# Llama 3.1 8B (~5 GB) — the default for your machine, fits in VRAM.
ollama pull llama3.1:8b

# An embedding model (~270 MB). Turns text into vectors.
ollama pull nomic-embed-text
```

With your RTX 5060 Ti + 32 GB RAM you can also try:

```powershell
ollama pull qwen2.5:14b      # smarter, slightly slower (mixes VRAM + RAM)
ollama pull phi4             # Microsoft's 14B, very capable
ollama pull llama3.2:3b      # tiny fallback if you ever want max speed
```

Then edit `LLM_MODEL` in `config.py` to switch between them.

## Step 3 — Set up the Python environment

From inside this project folder, in PowerShell:

```powershell
# Create a virtual environment so dependencies don't pollute your system Python
python -m venv .venv

# Activate it
.venv\Scripts\Activate.ps1

# If PowerShell blocks the activation script with an execution policy error,
# run this once (it only affects the current PowerShell session):
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Install dependencies
pip install -r requirements.txt
```

When the venv is active you'll see `(.venv)` at the start of your prompt.

## Step 4 — Add some documents

Put any PDFs or `.txt` files you want to chat with into the `docs/` folder.
A sample file is included so you can test right away.

## Step 5 — Ingest the documents

This reads your docs, chunks them, embeds each chunk, and stores them in a
local vector database (a folder called `chroma_db/`).

```bash
python ingest.py
```

You should see output like:

```
Loading documents from docs/
  - sample_private_llms.txt  (12 chunks)
Embedding 12 chunks with nomic-embed-text...
Done. Stored 12 chunks in chroma_db/
```

Re-run this any time you add, change, or remove documents.

## Step 6 — Chat with your docs

```powershell
python chat.py
```

You'll get a prompt:

```
Ask My Docs (model: llama3.1:8b) — type 'quit' to exit.

You: What is RAG?
Assistant: ...
Sources:
  - rag.md (chunk 2)
  - sample_private_llms.txt (chunk 4)
```

## Step 7 — Take a quiz on what you've indexed

The project ships with seven in-depth knowledge documents in `docs/`
covering **AI governance, RAG, MCP, embeddings, chunking, agent
architecture, and vector search**. Once you've run `python ingest.py`,
you can quiz yourself on any of them:

```powershell
python quiz.py
```

You'll see a numbered menu of topics. Pick one (or "Random"), and the
local LLM will generate 5 multiple-choice questions grounded in the
indexed material, score your answers, and show explanations.

You can also pass a topic directly:

```powershell
python quiz.py --topic "vector search" --n 10
python quiz.py --topic random
python quiz.py --topic "my own custom topic"
```

The quiz works on whatever is in your `chroma_db/` — drop your own
study materials into `docs/`, re-ingest, and quiz yourself on those.

## What's going on under the hood

Open the Python files — they're heavily commented. The whole thing is under
200 lines of code. Key concepts you'll see:

- **Chunking** — LLMs have a limited context window, so we slice docs into
  ~500-character pieces with some overlap so ideas aren't cut in half.
- **Embeddings** — each chunk becomes a vector (a list of ~768 numbers)
  capturing its meaning. Similar meanings → similar vectors.
- **Vector search** — your question gets embedded the same way, then we find
  the chunks whose vectors are closest to it (cosine similarity).
- **Prompt construction** — we stuff those chunks into a prompt template and
  ask the LLM to answer using only that information, so it doesn't make things up.

## Things to try next

1. **Swap the model.** Edit `LLM_MODEL` in `config.py` to try a bigger model
   (`llama3.1:8b`, `qwen2.5:14b`, `mistral`). See how the quality changes.
2. **Tune retrieval.** Change `TOP_K` in `config.py` from 4 to 2 or 8 and see
   how it affects answers.
3. **Add a web UI.** Try `pip install gradio` and wrap `answer_question()` in
   a Gradio interface — about 10 extra lines of code.
4. **Try structured output.** Have the LLM return JSON (e.g., extract names,
   dates, action items from your docs).
5. **Go bigger.** Once you're comfortable, look at LlamaIndex or LangChain
   — they're production-grade versions of what you just built by hand.

## Troubleshooting (Windows-specific notes inline)

- **"Connection refused" when running `chat.py`** — Ollama isn't running.
  Look for the Ollama icon in your system tray; if it's not there, open the
  Ollama app from the Start menu. You can also run `ollama serve` in PowerShell.
- **`python` isn't recognized** — the Python installer needs the "Add Python
  to PATH" checkbox ticked. 