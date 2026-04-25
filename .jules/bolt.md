## 2025-03-03 - SQLAlchemy Optimization: `.any()`/`.has()` vs `.join()`
**Learning:** In SQLAlchemy, filtering by relationships using `.join()` combined with `.limit()` causes incorrect results (returning fewer items than requested) because Python-side deduplication (like `.unique()`) happens *after* the limit is applied.
**Action:** Always prefer generating an `EXISTS` subquery via `.any()` or `.has()` instead of `.join()` when filtering by a relationship. This removes the need for `.distinct()` or `.unique()`, guaranteeing accurate pagination counts and results.
