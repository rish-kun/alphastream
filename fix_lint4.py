import os
for file in ["backend/app/models/news.py", "backend/app/models/portfolio.py", "backend/app/models/stock.py"]:
    with open(file, "r") as f:
        content = f.read()

    if "from typing import TYPE_CHECKING" not in content:
        content = "from typing import TYPE_CHECKING\n" + content

    if file == "backend/app/models/news.py":
        if "if TYPE_CHECKING:\n    from app.models.sentiment import SentimentAnalysis\n    from app.models.stock import Stock" not in content:
            content += "\n\nif TYPE_CHECKING:\n    from app.models.sentiment import SentimentAnalysis\n    from app.models.stock import Stock\n"
    elif file == "backend/app/models/portfolio.py":
        if "if TYPE_CHECKING:\n    from app.models.stock import Stock" not in content:
            content += "\n\nif TYPE_CHECKING:\n    from app.models.stock import Stock\n"
    elif file == "backend/app/models/stock.py":
        if "if TYPE_CHECKING:\n    from app.models.news import ArticleStockMention\n    from app.models.sentiment import AlphaMetric\n    from app.models.portfolio import PortfolioStock" not in content:
            content += "\n\nif TYPE_CHECKING:\n    from app.models.news import ArticleStockMention\n    from app.models.sentiment import AlphaMetric\n    from app.models.portfolio import PortfolioStock\n"

    with open(file, "w") as f:
        f.write(content)
