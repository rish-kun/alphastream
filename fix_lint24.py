import os
file = "backend/app/tests/test_sentiment.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('''    async def test_reanalyze_dispatches_existing_articles(
        self, client: AsyncClient, mock_db: AsyncMock
    ):
        article_id = uuid.uuid4()
        mock_db.execute.return_value = MockResult(data=[article_id])

        with patch("app.api.v1.sentiment._celery_app.send_task") as mock_send_task:
            mock_send_task.return_value = MagicMock(id="task-123")

            resp = await client.post(
                "/api/v1/sentiment/reanalyze",
                json={"article_ids": [str(article_id)], "force_reanalyze": True},
            )

        assert resp.status_code == 202
        assert resp.json()["task_id"] == "task-123"
        mock_send_task.assert_called_once()''', '''    async def test_reanalyze_dispatches_existing_articles(
        self, client: AsyncClient, mock_db: AsyncMock
    ):
        article_id = uuid.uuid4()
        mock_db.execute.return_value = MockResult(data=[article_id])

        with patch("app.api.v1.sentiment._celery_app.send_task") as mock_send_task, patch("app.api.v1.sentiment.ReanalysisStatusService.start_reanalysis") as mock_start:
            mock_send_task.return_value = MagicMock(id="task-123")
            mock_start.return_value = None

            resp = await client.post(
                "/api/v1/sentiment/reanalyze",
                json={"article_ids": [str(article_id)], "force_reanalyze": True},
            )

        assert resp.status_code == 202
        assert resp.json()["task_id"] == "task-123"
        mock_send_task.assert_called_once()''')

content = content.replace('''    async def test_reanalyze_all_dispatches_job(
        self, client: AsyncClient, mock_db: AsyncMock
    ):
        with patch("app.api.v1.sentiment._celery_app.send_task") as mock_send_task:
            mock_send_task.return_value = MagicMock(id="task-all")

            resp = await client.post("/api/v1/sentiment/reanalyze/all")

        assert resp.status_code == 202
        assert resp.json()["task_id"] == "task-all"
        mock_send_task.assert_called_once()''', '''    async def test_reanalyze_all_dispatches_job(
        self, client: AsyncClient, mock_db: AsyncMock
    ):
        with patch("app.api.v1.sentiment._celery_app.send_task") as mock_send_task, patch("app.api.v1.sentiment.ReanalysisStatusService.start_reanalysis") as mock_start:
            mock_send_task.return_value = MagicMock(id="task-all")
            mock_start.return_value = None

            resp = await client.post("/api/v1/sentiment/reanalyze/all")

        assert resp.status_code == 202
        assert resp.json()["task_id"] == "task-all"
        mock_send_task.assert_called_once()''')

with open(file, "w") as f:
    f.write(content)
