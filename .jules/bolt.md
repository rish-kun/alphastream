## 2026-03-03 - [Resolve N+1 query in get_sector_sentiment]
**Learning:** In SQLAlchemy with PostgreSQL, when fetching top N items for multiple groups (e.g. sectors), doing it in a loop results in an N+1 query problem.
**Action:** Use a single SQLAlchemy query combining a window function like `func.row_number()` partitioned by the group to deduplicate and rank efficiently, filtering for the top N items in the outer/sub query.
