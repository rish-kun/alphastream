from pathlib import Path

p = Path('pipeline/pipeline/tasks/sentiment_analysis.py')
content = p.read_text()
content = "from datetime import datetime, timezone\n" + content
p.write_text(content)

p = Path('pipeline/tests/test_llm.py')
content = p.read_text()
content = content.replace('with patch("pipeline.llm.gemini_client.genai", create=True) as mock_genai:', 'with patch("pipeline.llm.gemini_client.genai", create=True):')
p.write_text(content)
