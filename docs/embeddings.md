# Embeddings

An embedding is a fixed-length list of numbers that represents the meaning
of a piece of content — typically text, but the same idea applies to images,
audio, and code. Two pieces of content with similar meaning produce
embeddings that point in similar directions in a high-dimensional space.

Embeddings are the connective tissue of modern AI search: they let you ask
"what is this *about*?" rather than "what exact words does it contain?"

## The intuition

Imagine a 2D map where every word lives at some coordinate. "King" and
"queen" sit near each other. "King" and "monarchy" sit close. "King" and
"asparagus" sit far apart. Now extend that map from 2 dimensions to 384,
768, 1024, or 3072 dimensions — that is what an embedding model produces.

A famous (and somewhat simplified) demonstration:

```
embedding("king") - embedding("man") + embedding("woman") ≈ embedding("queen")
```

The geometry of the space encodes semantic relationships.

## What an embedding looks like

A 768-dimensional embedding for the sentence "The cat sat on the mat" is
simply a list of 768 floating-point numbers, e.g.

```
[0.0234, -0.1102, 0.0871, -0.0445, ..., 0.0093]   # 768 values
```

Stored as float32, that's 768 × 4 = 3,072 bytes per embedding. A million
chunks is 3 GB of vectors alone.

## How embedding models are trained

Most modern text embedding models are transformer encoders trained with
**contrastive learning**:

1. Construct pairs of "similar" texts (a question and its known answer,
   a sentence and its paraphrase, two captions of the same image).
2. Construct "dissimilar" pairs (random text from elsewhere in the corpus).
3. Train the model so similar pairs have cosine similarity close to 1 and
   dissimilar pairs close to 0.

Some models add multiple training stages:
- **Pretraining** on massive web-scale corpora with self-supervised
  objectives (masked language modeling).
- **Weakly supervised** contrastive training on mined pairs.
- **Supervised** fine-tuning on labeled retrieval datasets (MS MARCO,
  Natural Questions, BEIR).
- **Hard negative mining** — finding "tricky" negatives the model
  currently struggles to distinguish.

## Similarity metrics

Three are common; the choice depends on the model:

- **Cosine similarity** — the cosine of the angle between two vectors,
  ranging from −1 to 1. Insensitive to magnitude. Used by most embedding
  models because their training objective normalizes vectors.
- **Dot product** — like cosine, but sensitive to magnitude. Some models
  produce magnitude-meaningful embeddings (e.g. for confidence-weighted
  retrieval).
- **Euclidean (L2) distance** — straight-line distance in the embedding
  space. Equivalent to cosine for unit-normalized vectors. Less common
  for text but standard for some image and biology embeddings.

If you don't know which to use: check the model card. Most modern text
models specify cosine similarity and ship with normalized vectors.

## Embedding model families

### Closed / API-based
- **OpenAI** `text-embedding-3-small` (1536d, $0.02/1M tokens),
  `text-embedding-3-large` (3072d, $0.13/1M tokens).
- **Cohere** `embed-v3` (1024d, with input-type variants:
  `search_document`, `search_query`, `classification`, `clustering`).
- **Voyage AI** `voyage-3-large`, `voyage-code-3` — strong domain
  performance.

### Open weights (run locally or self-hosted)
- **BGE family** (BAAI) — `bge-large-en-v1.5`, `bge-m3` (multilingual,
  supports dense + sparse + multi-vector retrieval in one model).
- **Nomic** — `nomic-embed-text` (768d), an open, Apache-licensed model
  competitive with closed APIs.
- **Jina** — `jina-embeddings-v3`, strong long-context support (8192
  tokens) and multilingual coverage.
- **mxbai-embed-large-v1** — Apache-licensed, 1024d, popular on Ollama.
- **all-MiniLM-L6-v2** — 384d, tiny (~80 MB), the workhorse of small
  semantic-search projects.

### Specialized
- **Code embeddings** — `voyage-code`, `codesage`, `cosqa`. Trained
  primarily on code/docstring pairs.
- **Multimodal** — CLIP and successors (SigLIP, EVA-CLIP) embed images
  and text into a shared space.
- **Domain-specific** — `BioBERT-embed` for biomedical, `SecBERT-embed`
  for security, `FinBERT-embed` for finance.

## Dimensionality trade-offs

| Dim  | Notes |
|------|-------|
| 384  | Tiny models (MiniLM). Fast and cheap, lower ceiling. |
| 768  | Sweet spot for most workloads (nomic-embed-text, BGE-base). |
| 1024 | Strong general-purpose (BGE-large, mxbai). |
| 1536 | Frontier closed APIs (OpenAI `text-embedding-3-small`). |
| 3072 | Top of the range (OpenAI `text-embedding-3-large`). |

Higher dimensions can encode more nuance but cost more to store, transfer,
and search. For most production workloads, 768–1024 is the right zone.

## Matryoshka embeddings (MRL)

A 2024 training technique that produces embeddings whose *first N* dimensions
are themselves usable as smaller embeddings. You train once at the full
dimension, then truncate to whatever size your storage and latency budget
allow — without retraining. OpenAI's `text-embedding-3-*` models support
this, as do BGE-M3 and several others.

This lets you store full-precision embeddings for high-recall retrieval and
truncated versions for fast first-stage filtering.

## Common gotchas

### Asymmetric retrieval

Questions and answers often have different surface forms. The question
"How do I refund?" doesn't look like the answer "All returns within 30
days qualify for refund." Two solutions:

- **Asymmetric models** — train and use different prefixes for queries vs
  documents (e.g. nomic uses `search_query:` and `search_document:`
  prefixes; Cohere has `input_type` parameters).
- **HyDE** — generate a fake answer with the LLM, embed that for
  retrieval.

### Distribution shift

If you embed documents with model A and queries with model B (or with a
later version of A), distances are meaningless. Always use the *same*
model for both, and re-embed the corpus when you upgrade the model.

### Domain mismatch

A general-purpose embedding model trained on web text may perform poorly
on legal contracts, biomedical literature, or source code. Test on a held-
out set of your real queries before committing to a model.

### Token limit

Embedding models have a maximum input length, typically 512 to 8192
tokens. Longer inputs are truncated, often silently. If your chunks
exceed the limit, important content is lost.

### Embeddings are not for sentiment

A high-cosine-similarity pair just means the texts are *about* similar
things, not that they *agree*. "Vaccines cause autism" and "Vaccines
do not cause autism" have very similar embeddings. Don't use embeddings
for classification of agreement, sentiment, or truth — use them for topic.

### Multilingual collapse

A multilingual model embeds "dog" in English and "perro" in Spanish
close together, which is great for cross-lingual search but problematic
if you wanted language-aware separation. Use a monolingual model when
language identity matters.

## Practical evaluation

The MTEB leaderboard (Massive Text Embedding Benchmark) is the standard
public benchmark. It covers retrieval, reranking, classification, STS
(semantic textual similarity), clustering, and pair classification across
many languages.

For your own use case, build a small internal eval:

1. Collect 50–200 real questions from your domain.
2. Manually identify which document(s) actually answer each.
3. For each candidate embedding model: embed the corpus, embed the
   questions, measure Recall@5 and MRR.

A 30-minute internal eval beats any leaderboard for picking the right
model for *your* data.

## Storage and compression

For large corpora:

- **Int8 quantization** — 4× smaller than float32, typically 1–2% recall
  loss. Most vector DBs support this transparently.
- **Binary quantization** — 32× smaller, larger recall loss; pair with a
  reranking stage to recover quality.
- **Product quantization (PQ)** — used in FAISS IVF-PQ indexes; can
  compress aggressively while keeping search fast.
- **Matryoshka truncation** — store full dimensions, truncate at query
  time per use case.

## Glossary

- **Dimension** — the length of the embedding vector (e.g. 768).
- **Cosine similarity** — angle-based similarity, range [−1, 1].
- **Contrastive learning** — training paradigm that pulls similar pairs
  together and pushes dissimilar pairs apart.
- **Hard negative** — a "tricky" example that's similar to the positive
  but not actually relevant; key to good retrieval training.
- **Pooling** — turning the per-token outputs of a transformer into a
  single fixed-length vector (mean, CLS, attention pooling).
- **Normalization** — scaling a vector to unit length so cosine similarity
  reduces to dot product.
- **MTEB** — Massive Text Embedding Benchmark, the public leaderboard.
- **Symmetric / asymmetric** — whether queries and documents use the
  same encoder and prompts.
- **MRL / Matryoshka** — a training technique producing nestable
  embeddings.
- **HyDE** — Hypothetical Document Embeddings, query rewriting via LLM.
- **Embedding drift** — meaningful change in embedding distributions
  over time, often from model upgrades; invalidates existing indexes.
