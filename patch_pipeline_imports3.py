from pathlib import Path
p = Path('pipeline/pipeline/tasks/sentiment_analysis.py')
lines = p.read_text().splitlines()
lines.remove("from datetime import datetime, timezone")

# insert it after `from math import ceil`
idx = lines.index("from math import ceil")
lines.insert(idx + 1, "from datetime import datetime, timezone")

content = "\n".join(lines) + "\n"
p.write_text(content)
