## 2024-05-17 - [SQLAlchemy Performance: Optimizing Loop N+1]
**Learning:** When generating multiple result sets for multiple subgroups (like getting the top N stocks for every sector), iterating through the outer groups and executing a new query for each (`.limit(N)`) creates a severe N+1 problem.
**Action:** Replace loop-based queries with a single query using window functions (`func.row_number().over(partition_by=...)`) and join/filter correctly. When testing this, be sure to update `mock_db.execute.side_effect` to provide a single `MockResult` containing the pre-grouped, combined dataset.
