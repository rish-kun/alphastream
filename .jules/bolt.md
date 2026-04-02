## 2025-04-02 - Resolving N+1 queries for Top N Items per Group
**Learning:** In the PostgreSQL backend, fetching the "top N items per group" (e.g., top 5 stocks per sector) using a loop causes severe N+1 query performance degradation.
**Action:** Always pre-fetch and deduplicate "top N items per group" in a single query by utilizing SQLAlchemy `.distinct(*columns)` (translates to PostgreSQL `DISTINCT ON`) combined with `.order_by()` and `func.row_number() OVER (PARTITION BY group_col)`.
