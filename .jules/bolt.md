## 2025-01-01 - PostgreSQL DISTINCT ON for N+1 Deduplication
**Learning:** In the backend app (using SQLAlchemy on PostgreSQL), deduplicating records by grouping to find the most recent/relevant row per group in Python logic (`seen_windows.add(...)`) can pull immense unnecessary data into memory.
**Action:** Use PostgreSQL's `DISTINCT ON` feature via SQLAlchemy's `.distinct(*columns)` combined with `.order_by(*columns, sort_column.desc())` to perform fast, database-level deduplication without memory overhead.
