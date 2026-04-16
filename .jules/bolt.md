## 2026-03-03 - [SQLAlchemy 1-to-Many Pagination Pagination Bug]
**Learning:** Using `.join()` on a one-to-many relationship before applying a `.limit()` can result in returning fewer unique top-level items than the requested limit if deduplication (`.unique()`) happens on the Python side, as the limit applies to the Cartesian product rows.
**Action:** Always prefer `.any()` / `EXISTS` subqueries over `.join()` when filtering by one-to-many relationships just to check existence, to avoid database row duplication and correctly apply limits.
