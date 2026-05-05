## 2025-05-05 - Optimize Sentiment Aggregations
**Learning:** In SQLAlchemy, executing multiple distinct aggregation queries sequentially (e.g. `count()` for different conditions) on the same dataset causes N+1 round-trips and adds latency.
**Action:** Use a single database query with conditional aggregation via `func.count(case(...))` to calculate multiple metrics simultaneously, eliminating redundant query overhead.
