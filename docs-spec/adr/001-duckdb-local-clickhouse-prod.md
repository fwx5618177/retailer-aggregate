# ADR-001: DuckDB for Local Development, ClickHouse for Production Serving

> Status: Accepted
> Date: 2026-02-25
> Deciders: Engineering Team
> Supersedes: None
> Superseded by: None

## Context

The SEA Retailer Intelligence Platform needs an analytical database to serve the Gold layer (insights_daily and aggregated metrics) for API queries. The database must support:

1. **Fast analytical queries**: Filtering, sorting, and aggregating over ~3,600 rows/day (growing over time with data retention).
2. **Columnar storage**: Efficient compression and query performance for wide tables with many nullable fields.
3. **SQL interface**: Standard SQL for query authoring, testable by all team members.
4. **Two deployment contexts**:
   - **Local development**: Single developer on a laptop. Zero infrastructure dependencies. Fast iteration.
   - **Production**: Multi-user access via the API. Higher throughput. Operational reliability.

We evaluated the following options for the serving layer:

### Option A: PostgreSQL for both local and prod

- Pros: Familiar, mature, excellent tooling, works locally and in production.
- Cons: Row-oriented storage is suboptimal for analytical queries. Requires schema management (migrations). Requires running a database server even locally.

### Option B: DuckDB for both local and prod

- Pros: Zero-config, embedded, columnar, excellent Parquet support, fast analytical queries.
- Cons: Single-process access model. No built-in network server. Not designed for concurrent multi-user production workloads. Limited operational tooling (monitoring, backups, replication).

### Option C: ClickHouse for both local and prod

- Pros: Purpose-built for analytical queries. Columnar. Excellent compression. Scales horizontally. Built-in replication.
- Cons: Heavy for local development. Requires Docker or native installation. Configuration complexity. Overkill for a single developer running 3,600 rows.

### Option D: DuckDB for local, ClickHouse for prod (Chosen)

- Pros: Best tool for each context. Zero-config local dev. Production-grade analytics serving in prod.
- Cons: Two different databases to maintain compatibility for. Queries must work on both.

## Decision

We will use **DuckDB** as the Gold-layer serving database for local development and **ClickHouse** as the Gold-layer serving database for production.

## Rationale

### Why DuckDB for Local Development

1. **Zero configuration**: DuckDB is an embedded database. It runs in-process with no server to install, configure, or manage. A single file is the entire database. This removes a major friction point for developer onboarding.

2. **Native Parquet support**: DuckDB reads Parquet files directly with `SELECT * FROM 'file.parquet'`. Since our Bronze and Silver layers are stored as Parquet files, DuckDB provides a seamless bridge between the file-based pipeline layers and the SQL-based serving layer.

3. **Fast for analytical queries**: Despite being embedded, DuckDB is optimized for OLAP workloads. It uses columnar execution, vectorized processing, and automatic parallelism. For our data volumes (< 100K rows in local dev), queries complete in milliseconds.

4. **Python-native**: DuckDB has a first-class Python API (`import duckdb`). It integrates naturally with our Python pipeline and FastAPI API layer.

5. **Portable**: The DuckDB file can be copied, shared, and version-controlled. A developer can share their entire Gold-layer database as a single file for debugging.

### Why ClickHouse for Production

1. **Concurrent access**: ClickHouse is a client-server database that handles concurrent queries from multiple API server instances. DuckDB's single-process model is not suitable for this.

2. **MergeTree engine**: ClickHouse's MergeTree table engine provides efficient inserts, automatic data compaction, and partition management. This aligns with our daily-batch write pattern.

3. **Compression**: ClickHouse achieves 10-20x compression ratios on our data shape (many nullable fields, repeated strings like brand names and categories). This reduces storage costs as data accumulates.

4. **Operational tooling**: ClickHouse has built-in system tables for monitoring query performance, storage usage, and replication status. This is essential for production operations.

5. **Horizontal scalability**: While not needed for MVP, ClickHouse can scale to handle much larger data volumes (more categories, more countries) without architectural changes.

### Why Parquet as the Interchange Format

The key to making this dual-database strategy work is **Parquet** as the interchange format between pipeline layers and between local/prod environments:

```
Pipeline Output (Parquet files)
    |
    +--> DuckDB (local dev): Direct Parquet read/import
    |
    +--> ClickHouse (prod): Parquet import via INSERT INTO ... FROM input('parquet')
```

Both DuckDB and ClickHouse have native Parquet read support. The same Parquet files produced by the Insights module can be loaded into either database without transformation.

### Compatibility Layer

To ensure queries work on both databases, we adopt the following constraints:

1. **Standard SQL only**: Use ANSI SQL features that both databases support. Avoid database-specific functions.
2. **Query abstraction**: The API layer uses a thin query abstraction that generates compatible SQL for both backends.
3. **Type alignment**: Use types that map cleanly between DuckDB and ClickHouse:

| Logical Type | DuckDB Type | ClickHouse Type |
|-------------|-------------|-----------------|
| String | VARCHAR | String |
| Integer | INTEGER | Int32 |
| Big Integer | BIGINT | Int64 |
| Decimal | DECIMAL(p,s) | Decimal(p,s) |
| Boolean | BOOLEAN | UInt8 (0/1) |
| Date | DATE | Date |
| Timestamp | TIMESTAMP | DateTime |
| JSON | JSON | String (JSON serialized) |

4. **Integration tests**: Run the same query test suite against both DuckDB (in CI) and ClickHouse (in staging) to catch compatibility issues early.

## Consequences

### Positive

- Developers can start working immediately without installing any database server.
- Local development is fast and self-contained (single DuckDB file).
- Production serving is reliable and scalable with ClickHouse.
- Parquet interchange means we are not locked into either database. We could swap ClickHouse for another columnar DB (e.g., Apache Doris) with minimal changes.

### Negative

- Two databases to understand and maintain query compatibility for.
- Boolean handling differs (DuckDB: native BOOLEAN, ClickHouse: UInt8). Requires careful mapping.
- JSON handling differs (DuckDB: native JSON, ClickHouse: String with JSON functions). Complex JSON queries must be tested on both.
- Developers must resist the temptation to use DuckDB-specific features (e.g., `PIVOT`, list types) in the serving layer.

### Risks

- **Query drift**: Over time, queries may accumulate database-specific syntax. Mitigated by CI testing on both backends.
- **ClickHouse complexity**: ClickHouse has a learning curve for operations (engine selection, partition management, TTL). Mitigated by starting with a simple MergeTree setup.
- **DuckDB concurrency in tests**: Running parallel tests against the same DuckDB file can cause lock contention. Mitigated by using separate DuckDB files per test suite.

## Alternatives Considered

See the Options section above. The key rejected alternatives were:
- **PostgreSQL**: Row-oriented storage is a poor fit for analytical queries.
- **DuckDB-only**: Not suitable for concurrent production access.
- **ClickHouse-only**: Too heavy for local development.

## Related Documents

- [../design/system-design.md](../design/system-design.md) - Storage layer descriptions
- [../design/data-model.md](../design/data-model.md) - Table schemas that both databases implement
