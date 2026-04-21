import os
file = "backend/app/schemas/news.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace("from app.schemas.sentiment import SentimentResponse", "from app.schemas.sentiment import SentimentResponse  # noqa: E402")

with open(file, "w") as f:
    f.write(content)
