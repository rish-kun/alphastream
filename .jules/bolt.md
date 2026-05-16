## 2024-05-16 - [Optimize market sentiment aggregation query]
**Learning:** In SQLAlchemy, multiple aggregate queries over the same dataset (such as separate count queries for different conditions) can be optimized into a single database query using conditional aggregation with `func.count(case((condition, 1)))` to reduce database round-trips.
**Action:** Use conditional aggregation when querying for multiple summary statistics across the same group/condition to limit query volume.
