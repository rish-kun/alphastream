## 2025-05-06 - Single Query Aggregations in SQLAlchemy
**Learning:** Multiple separate `.count()` and `.avg()` queries hitting the same table (such as in `get_market_sentiment`) generate unnecessary network round-trips and repeated sequential scans.
**Action:** Always combine multiple aggregates over the same filtered dataset into a single query using conditional aggregation, i.e., `func.count(case((condition, 1)))`.
