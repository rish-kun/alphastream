from pathlib import Path
import re

# Fix sentiment_analysis.py
p = Path('pipeline/pipeline/tasks/sentiment_analysis.py')
content = p.read_text()
if 'from datetime import datetime, timezone' not in content:
    content = content.replace('from datetime import datetime\n', 'from datetime import datetime, timezone\n')
if 'asyncio.run(' in content and 'import asyncio' not in content:
    content = 'import asyncio\n' + content
p.write_text(content)

p = Path('pipeline/scripts/seed_pipeline.py')
content = p.read_text()
content = content.replace('from sqlalchemy import text\nfrom pipeline.database import get_db, check_schema_ready\n',
                          'from sqlalchemy import text  # noqa: E402\nfrom pipeline.database import get_db, check_schema_ready  # noqa: E402\n')
p.write_text(content)
