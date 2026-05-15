## 2025-03-04 - [Optimize Stock Alpha Deduplication with DISTINCT ON]
**Learning:** Historical data fetches (like alpha metrics over time) that require only the latest row per grouping can pull thousands of redundant rows into Python memory when deduplication is handled application-side.
**Action:** Always offload "latest-per-group" deduplication to the database layer. In PostgreSQL, `DISTINCT ON` combined with `ORDER BY` is a powerful tool to handle this natively, which can be implemented in SQLAlchemy using `.distinct(Column)` with an appropriate `.order_by()`.
