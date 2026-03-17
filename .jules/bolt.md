## 2026-03-17 - [Backend Query Optimization]
**Learning:** Combining multiple aggregate queries (like count/avg with different conditions) into a single query using SQLAlchemy's `func.count().filter(...)` can significantly reduce database round-trips.
**Action:** Always look for opportunities to batch related database queries, especially aggregations on the same table, using conditional aggregation (`FILTER WHERE`).
