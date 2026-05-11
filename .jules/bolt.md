## 2026-03-03 - [Optimize Sentiment Aggregation]
**Learning:** In SQLAlchemy, multiple aggregate queries over the same dataset (such as separate count queries for different conditions) can be combined into a single database query using conditional aggregation with `func.count(case((condition, 1)))` to reduce database round-trips.
**Action:** Always look for opportunities to combine multiple scalar/aggregate queries using `case` logic in SQL to reduce latency.
