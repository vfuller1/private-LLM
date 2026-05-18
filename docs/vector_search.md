# Vector Search

Vector search is the technique of finding items in a collection whose
embeddings are closest to a query embedding. It is the backbone of every
modern semantic search system, recommender, and RAG pipeline. Where keyword
search asks "which documents contain these exact words?", vector search
asks "which documents are *about* the same thing?"

## The basic problem

Given:
- A corpus of N items, each represented by a d-dimensional vector.
- A query vector q of the same dimension.

Return the K items most similar to q under some metric (usually cosine
similarity or Euclidean distance).

The naive solution is brute-force: compute the metric between q and every
one of the N vectors, then take the top K. Cost is O(N·d). For 10,000
vectors of dimension 768 this takes microseconds. For 100 million it
takes seconds — which is too slow for interactive use.

## Exact vs Approximate Nearest Neighbor

**Exact NN** — guarantees the true top-K. Brute-force at small scale,
or tree structures (kd-trees, ball trees) for low-dimensional data. Tree
methods break down above ~20 dimensions (the "curse of dimensionality"),
making them useless for embeddings.

**Approximate NN (ANN)** — gives the top-K with very high probability,
much faster. Accepts a small recall loss in exchange for orders-of-magnitude
speedup. Every modern vector database uses ANN.

The trade-off knob is the index's *recall* — what fraction of the true
top-K does the approximate search return? Production systems typically
target 95–99% recall.

## ANN algorithms

### HNSW (Hierarchical Navigable Small World)

The most popular ANN algorithm in 2024–2026. Builds a multi-layer graph
where each layer is a sparser approximation of the layer below. Search
starts at the top layer, greedily walks toward the query, then descends
to a more detailed layer.

- **Pros.** Very high recall at low latency. Excellent quality. Insertion
  is incremental (no rebuilds). Supported by every major vector DB.
- **Cons.** Memory-heavy (stores the graph). Slower to build than IVF.
  Deletion is awkward (most implementations soft-delete).

Key parameters:
- `M` — max connections per node per layer. Higher = better recall,
  more memory. Typical: 16–48.
- `efConstruction` — search effort during index build. Higher = better
  index, slower to build.
- `ef` — search effort at query time. Higher = better recall, slower
  query. Typical: 64–512.

### IVF (Inverted File index)

Clusters all vectors into K clusters using k-means. At query time,
search only the few clusters closest to the query.

- **Pros.** Fast indexing. Memory-efficient. Easy to reason about.
- **Cons.** Recall depends on cluster quality and `nprobe` (how many
  clusters to search). Inserts can degrade quality if clusters become
  unbalanced.

Often combined with **PQ (Product Quantization)** as **IVF-PQ** —
clusters compress the search space, and PQ compresses individual
vectors. Used heavily in Facebook AI Similarity Search (FAISS).

### ScaNN (Scalable Nearest Neighbors)

Google's algorithm, used in Vertex AI Matching Engine. Combines learned
partitioning with anisotropic quantization. Strong recall/latency
trade-off at very large scale.

### LSH (Locality-Sensitive Hashing)

Older method, mostly historical. Hash functions that put similar items
in the same bucket. Largely superseded by HNSW and IVF-PQ for embedding
search.

### Quantization techniques

These compress individual vectors, often combined with one of the above:

- **Scalar quantization (SQ)** — store each dimension as int8 instead
  of float32. 4× smaller, ~1% recall loss.
- **Product quantization (PQ)** — split the vector into M subvectors,
  cluster each independently, store cluster IDs. Massive compression
  (up to 64×) with larger recall loss; often paired with a re-scoring
  step using full-precision vectors for the top candidates.
- **Binary quantization** — each dimension becomes one bit. 32×
  smaller, biggest recall loss; reranking required.

## Distance metrics

- **Cosine similarity** — measures the angle between vectors, ignoring
  magnitude. Range [−1, 1], higher = more similar. The default for text
  embeddings.
- **Dot product** — like cosine but magnitude-sensitive. Used when the
  embedding model deliberately makes magnitude meaningful.
- **Euclidean (L2) distance** — straight-line distance. Lower = more
  similar. Common in image and biological embeddings.
- **Manhattan (L1) distance** — sum of absolute differences. Rare in
  embeddings.

For normalized vectors, cosine similarity and dot product are
equivalent, and Euclidean distance is a monotonic function of them —
so the ranking is the same regardless of which is used.

## Vector databases

The category exploded in 2023–2025. Major players:

**Self-hosted, open-source**
- **Chroma** — Python-first, file-based, dead simple. Great for
  prototyping and personal-scale RAG.
- **FAISS** — Facebook's library. Battle-tested, very fast, library
  not a database (no server, no metadata filtering on its own).
- **Qdrant** — Rust core, rich filtering, payload metadata, sparse
  vectors, scales well horizontally.
- **Weaviate** — strong schema and GraphQL API, built-in vectorization
  modules, hybrid search.
- **Milvus** — designed for very large scale, supports multiple index
  types, used in major Chinese companies.
- **pgvector** — PostgreSQL extension. Lives in your existing database.
  HNSW + IVF support. Massive ergonomic win if you already use Postgres.

**Managed / hosted**
- **Pinecone** — pioneer of the managed vector DB category, simple API.
- **Weaviate Cloud, Qdrant Cloud, Chroma Cloud** — managed versions
  of the open-source projects.
- **Vertex AI Matching Engine, Azure AI Search, OpenSearch k-NN** —
  cloud-native vector search in the hyperscalers.
- **Turbopuffer** — disk-based, designed for cost-efficient large scale.

**Hybrid search engines (vector + keyword)**
- **Elasticsearch / OpenSearch** — added vector support to existing
  text indexes; strong at hybrid.
- **Vespa** — Yahoo origins; mature vector + lexical + structured search.
- **Typesense** — lightweight, ergonomic, hybrid.

Choosing one: at < 1M vectors, almost anything works; pick on
ergonomics. At 10M–100M+, look at memory cost, query latency under
load, and how well metadata filtering composes with the vector
index.

## Hybrid search

Pure vector search misses things that pure keyword search catches:
exact product codes, rare proper nouns, dates, identifiers. Conversely,
keyword search misses synonyms, paraphrases, and conceptual matches.
Hybrid search combines both.

Two combination styles:

- **Score fusion** — run both searches, normalize the scores, blend
  with a weighted sum or use Reciprocal Rank Fusion (RRF, very common).
- **Filter then rank** — keyword filter narrows candidates, vector
  similarity ranks them.

Hybrid is almost always better than pure-vector for production
question-answering. The cost is a slightly more complex pipeline and
two index structures to maintain.

## Metadata filtering

Production retrieval is rarely "top-K from the entire corpus." It's
"top-K from chunks owned by the user's tenant, created after 2024,
tagged with 'policy'." Filtering interacts with ANN in subtle ways:

- **Pre-filter** — apply filter first, search only the matches. Correct
  but can degrade ANN performance if too few items remain (the index
  was built for the full set).
- **Post-filter** — search the full corpus, drop non-matches. Can
  return fewer than K items if the filter is selective.
- **Inline filter** — the ANN algorithm checks the filter as it
  traverses. Best of both worlds when supported (Qdrant, Pinecone,
  Weaviate, modern pgvector).

## Reranking

A two-stage architecture: a fast ANN retrieves top-50 (or 100, 200)
candidates, and a slower, more accurate **cross-encoder** reranker
re-scores each (query, chunk) pair. Final top-K (typically 3–10)
goes to the LLM.

Why it works: bi-encoders (the standard embedding model) embed query
and document independently, losing fine-grained interaction. Cross-
encoders score the pair together, capturing precise relevance.

Reranker model families:
- **bge-reranker** (BAAI) — strong, open weights.
- **mxbai-rerank** — fast, open weights.
- **Cohere Rerank** — closed API, very high quality.
- **Voyage Rerank** — closed API, strong domain performance.

Adding a reranker is one of the highest-impact, lowest-effort
improvements in any RAG system. The latency cost is meaningful (10s
to 100s of ms) but usually worth it.

## Performance tuning checklist

If retrieval quality is poor:

1. Measure Recall@K against a ground-truth set.
2. Verify the same embedding model is used for queries and corpus.
3. Try a better embedding model.
4. Add a reranker.
5. Add hybrid (BM25) search.
6. Inspect chunking — too small, too big, structure-broken?
7. Try query rewriting (HyDE, query expansion).

If retrieval latency is poor:

1. Increase `nprobe` (IVF) or `ef` (HNSW) reduction.
2. Quantize vectors.
3. Pre-filter with metadata before ANN.
4. Cache frequent queries.
5. Move from API-based embeddings to local ones.
6. Shard the index.

## Glossary

- **Vector / embedding** — fixed-length numeric representation of a
  piece of content.
- **ANN** — Approximate Nearest Neighbor.
- **Exact NN** — guarantees the true top-K, slower at scale.
- **HNSW** — Hierarchical Navigable Small World, the dominant ANN
  graph algorithm.
- **IVF** — Inverted File index; clusters and probes a few clusters.
- **PQ** — Product Quantization; aggressive vector compression.
- **IVF-PQ** — common combination.
- **Recall@K** — fraction of true nearest neighbors recovered in the
  top-K results.
- **Cosine similarity** — angle-based similarity, the default for text.
- **Dot product** — magnitude-sensitive similarity.
- **Hybrid search** — vector + keyword (BM25) combined.
- **BM25** — the standard keyword ranking function.
- **RRF** — Reciprocal Rank Fusion, a common score-merging method.
- **Cross-encoder** — model that scores (query, document) jointly;
  used for reranking.
- **Bi-encoder** — model that embeds query and document independently;
  used for first-stage retrieval.
- **Filter** — metadata predicate applied to the candidate set
  (pre, inline, or post the ANN search).
- **Index** — the data structure supporting fast retrieval.
- **Sharding** — splitting the index across multiple machines for
  scale.
