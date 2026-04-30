## 2024-04-30 - Optimize SQLAlchemy Relationship Filtering
**Learning:** Using `.join()` to filter on a one-to-many relationship in SQLAlchemy generates duplicate rows, which then requires `.distinct()` overhead and complex count queries.
**Action:** Prefer using `.any()` and `.has()` to generate an `EXISTS` subquery when filtering on related collections, which avoids duplicate rows and the need for `.distinct()` while maintaining accurate limits.
