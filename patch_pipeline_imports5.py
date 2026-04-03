from pathlib import Path
p = Path('pipeline/pipeline/tasks/sentiment_analysis.py')
lines = p.read_text().splitlines()
lines.remove("            import asyncio")
content = "\n".join(lines) + "\n"
p.write_text(content)
