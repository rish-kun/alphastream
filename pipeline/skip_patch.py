from pathlib import Path

content = Path("tests/test_deep_research_debug.py").read_text()
content = content.replace("def test_database_connection_skipped", "@pytest.mark.skip(reason=\"Requires live database connection\")\n    def test_database_connection_skipped")
Path("tests/test_deep_research_debug.py").write_text(content)
