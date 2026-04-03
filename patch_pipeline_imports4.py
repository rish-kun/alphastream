from pathlib import Path
p = Path('pipeline/pipeline/tasks/sentiment_analysis.py')
lines = p.read_text().splitlines()
lines.remove("import asyncio")
lines.insert(lines.index("import json") + 1, "import asyncio")
content = "\n".join(lines) + "\n"
p.write_text(content)
