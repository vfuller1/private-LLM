# Databricks, Delta Lake & the Medallion Architecture

The lakehouse is the dominant data architecture pattern in 2024–2026.
It combines the cost and flexibility of a data lake with the
transactional guarantees and performance of a data warehouse, on top of
open table formats sitting in cloud object storage.

Databricks is the leading commercial lakehouse platform, but the same
patterns apply to alternatives (Snowflake's Iceberg support, Microsoft
Fabric, Google BigLake, AWS Athena + Iceberg, Apache Hudi).

## Why lakehouses replaced traditional patterns

For two decades the standard pattern was:

- **Data lake** — cheap object storage, schema-on-read, great for raw and
  semi-structured data. Bad for ACID transactions, time-travel, and
  consistent analytics performance.
- **Data warehouse** — fast analytical queries, schema-on-write, ACID.
  Expensive at scale; awkward for unstructured data; vendor lock-in.

Most enterprises ended up with both, plus expensive ETL between them.
The lakehouse collapses the two by adding a transactional metadata layer
(Delta Lake, Apache Iceberg, Apache Hudi) on top of object storage,
preserving lake economics while delivering warehouse semantics.

## Delta Lake essentials

Delta is a storage layer that adds to Parquet:

- **ACID transactions** via an ordered transaction log (`_delta_log/`).
- **Time travel** — query any prior version of the table.
- **Schema enforcement and evolution** — writes that don't match the
  schema are rejected; evolution is explicit.
- **MERGE / UPSERT / DELETE** — first-class CDC operations on what used
  to be append-only files.
- **Z-ordering** — multi-dimensional clustering for skipping at query time.
- **Liquid clustering** — newer, dynamic alternative to Z-order and
  partitioning; recommended for new tables.
- **OPTIMIZE / VACUUM** — compaction of small files and cleanup of
  tombstoned data; both essential to long-term performance.
- **Deletion vectors** — soft deletes that don't require rewriting files;
  big efficiency win on update-heavy tables.

Delta files are still Parquet at rest — any compute engine that reads
Parquet can read the data, with caveats around log replay.

## The Medallion Architecture (Bronze / Silver / Gold)

A three-zone naming convention for organizing data within a lakehouse:

- **Bronze** — raw, append-only ingestion. Preserves the source as-is for
  reprocessing and auditability. Typically partitioned by ingest date.
- **Silver** — cleaned, conformed, deduplicated. Schemas are stable. This
  is where business rules and SCDs live.
- **Gold** — aggregated, business-facing tables and serving layers.
  Optimized for specific consumers (BI dashboards, ML features,
  operational APIs).

Common refinements:

- Some teams add **Diamond / Platinum** for ML feature stores and
  customer-facing analytics.
- Bronze tables can be append-only Delta or Auto Loader-fed; Silver and
  Gold use MERGE for upserts.
- Layer boundaries should align with ownership (Bronze owned by ingest
  team, Silver by data engineering, Gold by analytics/ML).

## Databricks platform components

- **Workspaces** — the UI / collaboration surface; notebooks, jobs, SQL.
- **Compute** — All-Purpose clusters (interactive), Job clusters
  (ephemeral, cheaper), SQL warehouses (Photon-accelerated, serverless),
  Model Serving endpoints, GPU compute for ML.
- **Photon** — Databricks' C++-rewritten query engine; significantly
  faster for SQL workloads.
- **Unity Catalog** — the central governance layer: catalogs / schemas /
  tables, ACLs, audit, lineage, data discovery. *Strongly preferred over
  legacy Hive metastore for any new deployment.*
- **Delta Live Tables (DLT)** — declarative ETL framework; you describe
  the desired tables and constraints, DLT figures out the dependency
  graph and orchestrates.
- **Auto Loader** — streaming ingestion that incrementally processes new
  files landing in object storage.
- **MLflow** — experiment tracking, model registry, deployment.
- **Genie / AI assistants** — natural-language interface for data
  exploration; powered by foundation models with grounding on your
  catalog.
- **Lakeflow** — Databricks' newer unified ingestion + transformation
  product, generalizing DLT.

## Unity Catalog (governance layer)

Unity is the most important architectural decision in a modern Databricks
deployment. It provides:

- **Three-level namespace** — `catalog.schema.table` replaces the older
  two-level Hive `database.table`.
- **Centralized ACLs** — GRANT/REVOKE at every level; column- and row-
  level masking.
- **Lineage** — automatic tracking of which tables flow into which,
  including upstream sources and downstream consumers.
- **Audit logs** — every read/write/grant.
- **External locations and storage credentials** — controlled mappings
  from Unity to underlying cloud storage paths.
- **Cross-workspace sharing** — one catalog can serve many workspaces
  in a region.
- **Delta Sharing** — open protocol for sharing live data across
  organizations and clouds without copying.

## Spark fundamentals for the architect

You don't need to write Spark every day, but you must understand:

- **DataFrames vs RDDs** — almost all modern code uses DataFrames /
  Datasets / Spark SQL. RDDs are legacy.
- **Lazy evaluation** — transformations build a DAG; actions
  (`.collect()`, `.write()`, `.count()`) trigger execution.
- **Shuffles** — wide transformations (joins, groupBy) reshuffle data
  across executors; expensive and the usual source of slow jobs.
- **Adaptive Query Execution (AQE)** — runtime plan adjustment for
  skew, join strategies, partitioning. Enable it (default in modern
  Spark).
- **Broadcast joins** — small tables get broadcast to every executor
  instead of shuffled; massive speedup for star schemas.
- **Partitioning** — physical layout on disk. Don't over-partition
  (small files problem); don't under-partition (full scans on
  large queries).

## File layout and performance

- **Small files problem** — too many tiny files slow down everything.
  Use OPTIMIZE / auto-compaction.
- **Partition pruning** — partition on low-cardinality, frequently-
  filtered columns (date is the canonical example). Never partition on
  user ID or other high-cardinality fields.
- **Z-order / liquid clustering** — within a partition (or instead of
  partitioning), cluster on columns commonly used in WHERE clauses.
- **File sizes** — target 100MB–1GB per file for analytical workloads.
- **VACUUM retention** — default 7 days; reduce only with care because
  it kills time travel and breaks readers mid-query.

## Streaming and CDC

- **Structured Streaming** — micro-batch (default) or continuous mode;
  the standard way to do streaming on Databricks.
- **Auto Loader** — recommended for ingesting from cloud storage.
- **Delta CDF (Change Data Feed)** — read what changed in a Delta table
  between versions; foundation for downstream CDC.
- **Materialized views** — incrementally maintained query results, served
  by Databricks SQL.

## Lakehouse alternatives

- **Snowflake** — added Iceberg table support; tightly integrated SQL;
  newer Cortex AI suite for embeddings, summarization, completion.
- **Microsoft Fabric** — Microsoft's unified lakehouse + warehouse +
  power BI offering; OneLake is the storage tier.
- **AWS Athena + Iceberg + Glue** — pieces, not a platform, but flexible.
- **Open-source stack** — Iceberg + Trino + dbt + Airflow is the
  vendor-neutral approach.

## Anti-patterns

- **Skipping Unity Catalog "because it's faster to start."** You will
  pay back the migration cost 10× later.
- **Using All-Purpose clusters for production ETL.** Use Job clusters;
  they're cheaper and don't drift.
- **Over-relying on notebooks for production code.** Notebooks are for
  exploration; production should be modular code with tests.
- **No data contracts at layer boundaries.** Schema changes in Bronze
  cascade unpredictably into Silver and Gold if there's no contract.
- **Treating Gold as the only "blessed" layer.** Silver is just as much
  a product; many ML features and analytics teams live there.

## Glossary

- **Lakehouse** — pattern combining lake economics with warehouse semantics.
- **Delta Lake** — Databricks-led open-source table format.
- **Apache Iceberg / Apache Hudi** — competing open table formats.
- **Medallion** — Bronze / Silver / Gold layered data architecture.
- **Unity Catalog** — Databricks governance layer.
- **DLT / Delta Live Tables / Lakeflow** — declarative ETL frameworks.
- **Auto Loader** — incremental file ingestion.
- **Photon** — Databricks' vectorized query engine.
- **AQE** — Adaptive Query Execution; runtime plan optimization.
- **Z-order / liquid clustering** — data clustering for skipping.
- **OPTIMIZE / VACUUM** — file compaction and cleanup.
- **MERGE** — SQL upsert; ACID atomic merge of changes.
- **Time travel** — query a prior version of a Delta table.
- **CDF** — Change Data Feed; emits the diff between table versions.
- **MLflow** — experiment tracking + model registry.
- **Delta Sharing** — open protocol for sharing live tables across orgs.
