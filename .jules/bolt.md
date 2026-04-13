## 2025-03-03 - [Optimize Pagination Queries Involving Joins]
**Learning:** Using `.join()` to filter items before applying `LIMIT` or `OFFSET` causes duplicate rows. Filtering via `EXISTS` (SQLAlchemy `.any()`) avoids duplication, speeds up pagination, and fixes bugs where deduplication occurs in-memory *after* `.limit()`, ensuring an accurate returned count.
**Action:** Replace `JOIN` with `.any()` subqueries when filtering for related collection matches during paginated fetches.
