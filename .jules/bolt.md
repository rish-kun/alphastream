## 2024-05-20 - N+1 Query in Sector Sentiment
**Learning:** The `get_sector_sentiment` endpoint previously used a loop to fetch the top stocks for each sector individually, resulting in an N+1 query problem. This codebase architecture benefits greatly from consolidating such repeated queries into a single query using window functions like `row_number() over (partition by ...)`.
**Action:** When working on similar grouping endpoints, always look for opportunities to replace Python-side loops over database queries with SQL window functions to reduce database round-trips.
