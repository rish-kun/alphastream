## 2024-03-03 - Database-Level Deduplication is Safe
**Learning:** The application safely relies on PostgreSQL-specific behavior. Using `.distinct(*columns)` in SQLAlchemy correctly translates to `DISTINCT ON`, allowing us to replace application-level deduplication loops with faster database-level operations.
**Action:** When seeing application-level loops that deduplicate `order_by` results, look to replace them with `.distinct(column)` in SQLAlchemy queries to reduce memory footprint and latency.
