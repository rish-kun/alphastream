## 2023-10-27 - [Avoid `.join()` + `.limit()` + `.unique()` for collections]
**Learning:** Combining SQL `.join()` with `.limit()` on relationships, then doing Python-side `.unique()` deduplication is a codebase anti-pattern that results in both slower performance (extra memory overhead) and bugs (returning fewer than `limit` results).
**Action:** Use `.any()` or `.has()` to generate an `EXISTS` subquery instead, to ensure deduplication occurs at the database level before the limit is applied.
