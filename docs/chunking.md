# Chunking

Chunking is the process of splitting a document into smaller pieces before
embedding it for retrieval. It is the most overlooked, least glamorous, and
most impactful design decision in a RAG system. A well-chunked corpus with
a mediocre model will outperform a poorly-chunked corpus with the best model
on the market.

## Why we chunk

Three reasons:

1. **Embedding model token limit.** Most embedding models accept 512 to
   8192 tokens. A 100-page PDF has tens of thousands of tokens and won't
   fit.
2. **Embedding quality.** Embeddings represent the *average meaning* of
   their input. A single embedding for a long document blends every topic
   it covers; specific questions don't match it well.
3. **LLM context budget.** Even with long-context models, you can't (and
   shouldn't) stuff entire documents into every prompt. Retrieval finds
   the relevant pieces; chunking creates those pieces.

## What goes wrong without good chunking

- **Mid-sentence splits.** A chunk that ends "The CEO resigned because" is
  useless without the rest of the sentence.
- **Floating references.** "This shall apply to all cases described above"
  in chunk 17 of a contract is meaningless when retrieved alone.
- **Header / body separation.** A heading like "Refund Policy" sits in
  one chunk, the actual policy text sits in the next. Neither is retrievable
  by its own merits.
- **Cross-topic blending.** A chunk that contains the end of one topic
  and the start of another averages to neither.
- **Information overload.** A chunk that's too large dilutes the relevant
  signal across too much surrounding text.

## Chunking strategies

### Fixed-size (character or token)

The naive baseline. Pick a size (e.g. 500 characters or 256 tokens) and an
overlap (e.g. 80 characters or 40 tokens). Slide a window through the text.

- **Pros.** Trivial to implement. Predictable chunk sizes. No dependency
  on document structure.
- **Cons.** Cuts sentences in half. No structural awareness. Same chunk
  size for a one-page memo and a 600-page textbook.

This is the right starting point. It's also where many production systems
stop and pay the price.

### Recursive character splitting

Pick an ordered list of separators (`\n\n`, `\n`, `. `, ` `). Try to split
on the first separator; if a piece is still too large, recurse with the
next. This is what LangChain's `RecursiveCharacterTextSplitter` does.

- **Pros.** Respects paragraph and sentence boundaries when possible.
  Falls back gracefully. Easy upgrade from naive fixed-size.
- **Cons.** Still no semantic awareness. Can produce wildly varying
  chunk sizes when the document has irregular structure.

### Sentence-level

Split on sentences (e.g. with spaCy's sentencizer or NLTK's
`sent_tokenize`), then group N sentences per chunk.

- **Pros.** Clean boundaries. Sentences are coherent semantic units.
- **Cons.** Sentence boundaries are surprisingly hard for languages
  without clear punctuation. Doesn't capture paragraph- or section-level
  context.

### Semantic chunking

Embed each sentence, then group consecutive sentences whose embeddings
are close. When the cosine similarity between two adjacent sentences
drops below a threshold, end the current chunk and start a new one.

- **Pros.** Chunks correspond to actual topic shifts in the document.
  Often dramatically better retrieval for argumentative or narrative text.
- **Cons.** Expensive — requires embedding every sentence at ingest
  time. Threshold needs tuning per corpus. Can produce extreme chunk
  size variance.

### Document-structure-aware

Use the document's own structure: markdown headings, HTML sections, PDF
bookmarks, DOCX styles, code class/function boundaries. Each chunk
becomes one structural unit, optionally subdivided if it exceeds a size
limit.

- **Pros.** Chunks align with how the author meant the content to be
  read. Headers can be prepended to bodies for context.
- **Cons.** Requires parsers that preserve structure. Poorly authored
  documents (one giant heading-less wall of text) defeat the strategy.

### Agentic / LLM-based chunking

Hand the document to an LLM and ask it to identify natural chunk
boundaries. Variants include having the LLM summarize sections and use
the summaries as retrieval targets.

- **Pros.** Highest quality on structurally complex documents.
- **Cons.** Expensive at ingest. Non-deterministic. Hard to debug.

### Late chunking / parent-document

Embed *short* chunks for precise retrieval, but at generation time, look
up and provide the *parent* (the surrounding paragraph, section, or
document) so the LLM sees full context.

- **Pros.** Best of both worlds — precise matching, rich context.
- **Cons.** Requires tracking the parent for each chunk. Larger
  generation prompts.

## Overlap

Chunk overlap is the number of characters or tokens at the end of one
chunk that also appear at the start of the next. A typical overlap is
10–20% of chunk size (e.g. 80 characters out of 500).

Why overlap matters: if a sentence containing the answer happens to fall
exactly on the boundary between two chunks, neither chunk alone tells
the full story. Overlap ensures every sentence appears in full in at
least one chunk.

Drawbacks: storage cost (more chunks), embedding cost, and slightly
higher chance of duplicate content in retrieval results. For most
projects, this is a worthwhile trade.

## Choosing chunk size

This is the most-asked question in RAG and the most-wrongly answered.
There is no universal best size. The right size depends on:

- **Embedding model's optimal range.** Some models perform best at
  256 tokens, others at 1024+. Check the model card.
- **The granularity of your questions.** "What's the refund window?"
  needs a small chunk. "Summarize section 4" needs a large chunk.
- **The structure of your documents.** Dense technical text packs more
  meaning per character than narrative prose.
- **Your top-K.** Smaller chunks with larger K can outperform large
  chunks with smaller K, or vice versa.

Practical guidance for English text:

| Chunk size | When |
|---|---|
| 128–256 tokens (~500–1000 chars) | Q&A over short factual passages, FAQs |
| 512 tokens (~2000 chars)         | Default for most general-purpose RAG |
| 1024 tokens (~4000 chars)        | Long-form reasoning, complex policies |
| 2048+ tokens                     | Whole-section retrieval, parent-doc patterns |

If unsure: start at 512 tokens with 50–100 token overlap, build an eval
set, then iterate.

## Metadata to keep with every chunk

Good chunks travel with context:

- **Source filename or URL.**
- **Page number** (for PDFs).
- **Section / heading hierarchy** (e.g. "Chapter 3 > Refunds > Eligibility").
- **Document title.**
- **Created/updated date.**
- **Author or document owner.**
- **Access control labels** (which users may see this chunk).

Why bother: metadata enables filtering at retrieval time ("only chunks
from 2024", "only chunks owned by Legal"), citations in answers, and
debugging when retrieval misbehaves.

## How to evaluate chunking choices

Chunking is a hyperparameter. Tune it like any other:

1. Build a small evaluation set: 30–100 real questions with the chunks
   you'd ideally want returned.
2. Hold the embedding model and retrieval pipeline constant.
3. Try several chunking strategies and sizes.
4. Measure Recall@K and the downstream answer quality.

You will be surprised how often "common-sense" choices fail and how
much a 20% chunk-size tweak can move the needle.

## Anti-patterns

- **One chunk per document.** Defeats the point of retrieval.
- **Splitting in the middle of code blocks, tables, or formulas.**
  Severely harms retrieval and generation.
- **Discarding metadata.** Makes citation and filtering impossible.
- **Re-chunking with different settings without re-embedding.** Mixed
  chunk sizes in the same index cause subtle quality drops.
- **Treating chunking as a one-time decision.** Documents change, models
  change, requirements change. Plan to re-chunk.

## Glossary

- **Chunk** — a piece of source text, sized for embedding.
- **Chunk size** — the target length of each chunk, measured in
  characters, tokens, or sentences.
- **Overlap** — content shared between consecutive chunks.
- **Splitter** — the algorithm that produces chunks from documents.
- **Recursive splitter** — tries a list of separators in order before
  falling back to character splits.
- **Semantic chunking** — splitting based on embedding similarity drops
  between sentences.
- **Parent document / late chunking** — retrieve on small chunks, then
  expand to larger surrounding context for generation.
- **Metadata** — structured fields attached to a chunk for filtering,
  citation, and access control.
- **Token** — the unit a language model actually reads; roughly 0.75
  English words on average.
