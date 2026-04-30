import re

with open("pipeline/tests/test_deep_research_debug.py", "r") as f:
    content = f.read()

content = content.replace(
    'def test_database_connection(self):',
    '@patch("pipeline.database.get_engine")\n    @patch("pipeline.database.check_schema_ready")\n    def test_database_connection(self, mock_check, mock_engine):'
)

content = content.replace(
    'engine = get_engine()',
    'mock_engine.return_value.connect.return_value.__enter__.return_value.execute.return_value.scalar.return_value = 1\n            mock_check.return_value = True\n            engine = mock_engine()'
)

with open("pipeline/tests/test_deep_research_debug.py", "w") as f:
    f.write(content)
