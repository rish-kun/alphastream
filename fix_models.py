import re
from pathlib import Path

def process_file(filepath):
    content = Path(filepath).read_text()
    if 'from typing import TYPE_CHECKING' not in content:
        content = content.replace('from sqlalchemy.orm import Mapped, mapped_column, relationship\n',
                                  'from typing import TYPE_CHECKING\nfrom sqlalchemy.orm import Mapped, mapped_column, relationship\n')

    # Fix app/models/news.py
    if 'news.py' in filepath and 'if TYPE_CHECKING:' not in content:
        content += """\n\nif TYPE_CHECKING:
    from app.models.sentiment import SentimentAnalysis
    from app.models.stock import Stock
"""
    # Fix app/models/portfolio.py
    if 'portfolio.py' in filepath and 'if TYPE_CHECKING:' not in content:
        content += """\n\nif TYPE_CHECKING:
    from app.models.stock import Stock
"""
    # Fix app/models/stock.py
    if 'stock.py' in filepath and 'if TYPE_CHECKING:' not in content:
        content += """\n\nif TYPE_CHECKING:
    from app.models.news import ArticleStockMention
    from app.models.sentiment import AlphaMetric
    from app.models.portfolio import PortfolioStock
"""
    Path(filepath).write_text(content)

process_file('backend/app/models/news.py')
process_file('backend/app/models/portfolio.py')
process_file('backend/app/models/stock.py')

schema_content = Path('backend/app/schemas/news.py').read_text()
if 'def _rebuild():' not in schema_content:
    schema_content = schema_content.replace(
        'from app.schemas.sentiment import SentimentResponse\n\nNewsArticleResponse.model_rebuild()',
        '''def _rebuild():
    from app.schemas.sentiment import SentimentResponse
    NewsArticleResponse.model_rebuild(_types_namespace={'SentimentResponse': SentimentResponse})

_rebuild()'''
    )
    Path('backend/app/schemas/news.py').write_text(schema_content)
