## 2026-05-13 - Optimizing Multiple Counts in SQLAlchemy
**Learning:** Using conditional aggregation (`func.count(case((condition, 1)))`) in a single SQLAlchemy statement can collapse multiple count/average queries over the same dataset into one database round-trip. This fundamentally saves DB connection overhead and query latency compared to individual statements.
**Action:** Always look for multiple adjacent `select(func.count())` queries filtering the same table and merge them using `.label()` and `case()`.
