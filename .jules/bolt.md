## 2025-04-08 - Use PostgreSQL DISTINCT ON for N+1 Deduplication
**Learning:** In the PostgreSQL backend, fetching global top N items per group and applying deduplication in Python memory is inefficient (especially when fetching multiple rows only to discard them in a loop with a `set()`).
**Action:** When filtering for the latest record per group across groups using SQLAlchemy, safely utilize `.distinct(*columns)` alongside `.order_by()` to take advantage of PostgreSQL's `DISTINCT ON` feature. This translates the deduplication to the query level.
