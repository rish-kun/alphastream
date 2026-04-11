## 2025-04-11 - PostgreSQL DISTINCT ON behavior with limit

**Learning:** When using SQLAlchemy `.distinct(*columns)` with `.limit()`, applying `.limit()` can result in returning fewer records than expected if the database query fetches duplicate records globally which are later stripped down by the Python code. However, applying `.distinct(*columns)` pushes deduplication to the PostgreSQL database `DISTINCT ON`, guaranteeing we get exactly one result per deduplication key before limits are applied, drastically reducing data transfer and Python object creation time for latest-record-per-group queries.

**Action:** For queries like "get the most recent alpha metric for each stock in a portfolio" or "get the most recent alpha metric per window size for a stock", use `DISTINCT ON` via `.distinct(column)` coupled with `.order_by(column, date.desc())`.
