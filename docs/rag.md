# Retrieval-Augmented Generation (RAG)

RAG is a pattern for connecting a language model to information outside its
training data. The model retrieves relevant documents at query time and
generates an answer grounded in that retrieved context. RAG is the dominant
way enterprises put LLMs to work on private data because it solves three
problems at once: stale knowledge, hallucination, and the impossibility of
fitting a whole corpus into a prompt.

## The core pattern

Every RAG system has the same three stages, regardless of complexity:

1. **Index (offline).** Documents are split into chunks, each chunk is
   converted to an embedding, and the embeddings are stored in a vector
   database.
2. **Retrieve (online).** The user's question is embedded the same way,
   and the database returns the chunks whose embeddings are most similar.
3. **Generate (online).** The retrieved chunks are inserted into a prompt
   template along with the question, and the LLM produces an answer.

The model never "learns" your documents — it just sees them as context for
each query. That's why RAG works with off-the-shelf models, no fine-tuning
required.

## Why RAG, not fine-tuning?

Fine-tuning teaches the model new behavior or style. RAG teaches it new
facts. Most of the time, the question is "what does this document say?",
not "how should you answer this kind of question?" — so RAG is the right
tool.

Practical comparison:

| | Fine-tuning | RAG |
|---|---|---|
| Goal | Change *how* the model responds | Give the model new *facts* |
| Update cost | Hours to days of GPU time per change | Re-embed and re-index (seconds) |
| Auditability | Hard — knowledge is baked into weights | Easy — answers cite retrieved chunks |
| Cost per query | Same as base model | Embed query + larger context = slightly more |
| Works with closed models | Only via the provider's fine-tuning API | Yes |

For most enterprise use cases, RAG is the default. Fine-tuning is reserved
for tasks where style, format, or domain reasoning matters more than factual
recall — for example, generating code in a particular framework's style.

## Naive RAG (the baseline)

The simplest implementation:

1. Fixed-size chunking (e.g. 500 characters with 80 character overlap).
2. Single embedding model for both chunks and queries.
3. Cosine similarity search for top-K chunks.
4. Stuff all retrieved chunks into the prompt.
5. Generate the answer.

This works surprisingly well as a starting point and is what most teams
build first. It is also the source of most RAG failures in production.

## How naive RAG fails

- **Lost in the middle.** LLMs pay less attention to information in the
  middle of long contexts than to information at the beginning or end.
  Stuffing 20 chunks into a prompt often produces worse answers than the
  best 4.
- **Bad retrieval.** Embedding similarity ≠ semantic relevance. The
  top-K chunks may be on the right *topic* but contain none of the actual
  facts needed to answer the question.
- **Question/answer asymmetry.** Embedding the question "What is the
  refund policy?" may not retrieve a chunk that *states* the refund policy
  without ever using the word "refund."
- **Chunking destroys context.** A chunk in the middle of a 100-page
  contract may say "this shall apply" — but without the preceding section
  header, the model can't tell what "this" refers to.
- **Multi-hop questions.** "Who was the CFO when revenue first exceeded
  $1B?" requires combining a financial chunk with an executive-history
  chunk, which naive retrieval rarely returns together.
- **Negation and exclusion.** "What products are NOT FDA approved?" tends
  to retrieve chunks about approved products.
- **Knowledge cutoff confusion.** The model may override retrieved facts
  with its own (older) training knowledge if the prompt isn't explicit.

## Advanced RAG techniques (in order of typical impact)

### Better chunking

- **Recursive chunking** — split on natural boundaries (paragraphs, then
  sentences) before resorting to character counts.
- **Semantic chunking** — embed sentences, group consecutive sentences
  whose embeddings are similar, split when similarity drops.
- **Document-aware chunking** — preserve structural metadata (headers,
  page numbers, section anchors) on each chunk.
- **Hierarchical chunking / small-to-big** — store both small chunks (for
  precise retrieval) and large chunks (for context), retrieve on small,
  expand to large before generation.

### Better retrieval

- **Hybrid search** — combine dense (vector) retrieval with sparse (BM25,
  keyword) retrieval. Vector search catches semantic matches, BM25 catches
  exact terms, names, and codes. Score-fuse the results.
- **Query rewriting** — use an LLM to expand or rephrase the query before
  embedding (HyDE — hypothetical document embeddings — generates a fake
  answer and uses its embedding for retrieval).
- **Query decomposition** — split multi-part questions into sub-queries,
  retrieve for each, merge.
- **Metadata filtering** — restrict retrieval by document date, author,
  type, etc., before similarity search.

### Reranking

A second-stage cross-encoder model (e.g. `bge-reranker`, `cohere-rerank`,
`mxbai-rerank`) scores each (query, chunk) pair more accurately than the
first-stage vector search. Typical pattern: retrieve top-50 with the vector
index, rerank to top-5, send those to the LLM. Reranking is one of the
highest-ROI improvements in any RAG system.

### Better prompting

- Explicit instructions to answer from context only.
- Refuse-to-answer ("say 'I don't know'") clauses.
- Citation requirements — make the model quote the source chunk.
- Chain-of-thought scratchpad before the final answer.

### Generation-time grounding

- **Citation enforcement** — post-process the output, verify every claim
  appears in the retrieved chunks (or in the union of retrieved chunks).
- **Self-RAG** — model is trained or prompted to decide when to retrieve
  more, and to critique its own output.
- **Verification with a second model** — a critic model checks the
  answer against the chunks and flags inconsistencies.

### Agentic RAG

The system is no longer a single pipeline. An agent decides when to
retrieve, what to retrieve, whether the results are good enough, and
whether to retry with a different query. This is the most flexible and
also the most expensive approach.

## Evaluating a RAG system

You cannot improve what you cannot measure. Standard RAG evaluation has
two halves:

**Retrieval quality** — given a question and a known set of relevant
chunks, did the retriever return them?

- **Recall@K** — fraction of relevant chunks among the top-K returned.
- **MRR (mean reciprocal rank)** — 1/rank of the first relevant chunk.
- **nDCG** — discounted cumulative gain, weights early positions more.

**Generation quality** — given the question and retrieved chunks, was the
answer correct, faithful, and useful?

- **Faithfulness** — does the answer say only what the chunks support?
- **Answer relevance** — does the answer address the question?
- **Context relevance** — did the retriever return useful chunks?

Frameworks like Ragas, TruLens, and DeepEval automate these metrics
using an LLM-as-a-judge approach. They are imperfect but indispensable.

## Storage costs at scale

A single 768-dimensional embedding stored as float32 occupies 3 KB.
A million chunks is 3 GB of vectors alone, plus the original text. Common
optimizations:

- **Quantization** — store vectors as int8 or even binary; ~4× to 32×
  smaller, small recall loss.
- **Dimensionality reduction** — use a smaller embedding model, or
  Matryoshka representation learning (MRL) embeddings which can be
  truncated.
- **Tiered storage** — hot index in RAM, cold in object storage.

## Glossary

- **Top-K** — the number of chunks returned by retrieval (typically 3–10).
- **Chunk** — a piece of source text small enough to embed cleanly.
- **Context window** — the maximum number of tokens an LLM can read in
  one prompt. Modern open-weight models range from 8K to 128K+.
- **Stuffing** — placing all retrieved chunks into the prompt verbatim.
- **HyDE** — Hypothetical Document Embeddings; use the LLM to generate
  a fake answer, then embed that for retrieval.
- **Recall** — fraction of relevant items the retriever found.
- **Precision** — fraction of returned items that are relevant.
- **Re-ranker** — a second-stage model that re-scores candidate chunks.
- **Grounded generation** — output that demonstrably uses only the
  provided context.
- **Index** — the data structure (HNSW, IVF-PQ, etc.) supporting
  approximate nearest-neighbor search over embeddings.
- **Embedding drift** — the same embedding model producing different
  vectors over time, usually after model updates; breaks retrieval.

## RAG in production: a maturity ladder

1. **Hello-world.** Single document, naive chunking, default settings.
2. **Useful.** Multi-document corpus, sensible chunking, hybrid retrieval,
   citations, basic eval harness.
3. **Production.** Reranking, query rewriting, monitoring, retraining
   pipeline, A/B framework, content-source freshness tracking.
4. **Agentic.** Self-correcting agent loop, multi-step retrieval, tool
   use, sophisticated eval covering safety, faithfulness, and helpfulness.

Most successful RAG deployments live at level 2 or 3. Jumping to level 4
without first nailing 2 is a common and expensive mistake.
