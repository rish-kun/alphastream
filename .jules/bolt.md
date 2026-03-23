
## 2025-03-03 - [Leveraging PostgreSQL's DISTINCT ON for deduplication]
**Learning:** In the PostgreSQL backend, fetching history and deduplicating in Python using loops (O(n)) can result in massive overhead by transferring large amounts of data to the application layer. `DISTINCT ON` provides a significant optimization for ordered deduplication by handling this at the query level.
**Action:** Use SQLAlchemy's `.distinct(*columns)` alongside `order_by` (matching the columns and optionally adding order criteria like `.desc()`) to avoid N+1 issues and memory bottlenecks when only the most recent/relevant records per group are needed.
