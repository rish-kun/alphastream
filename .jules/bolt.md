## 2025-03-03 - [Eliminating PostgreSQL N+1 query patterns using DISTINCT ON]
**Learning:** PostgreSQL's DISTINCT ON feature combined with window functions (like row_number) can efficiently batch fetching the "top N items per group" across multiple groups. In SQLAlchemy, this allows replacing O(N) sector loop queries into a single deduplicated O(1) query.
**Action:** Always scan loops querying identical relations with varying filters for batching opportunities. Use DISTINCT ON early in subqueries when multiple joins might introduce duplicates, then rank items with row_number.
