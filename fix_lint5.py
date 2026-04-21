import os
for file in ["backend/app/models/news.py", "backend/app/models/portfolio.py", "backend/app/models/stock.py"]:
    with open(file, "r") as f:
        content = f.read()

    content = content.replace("from typing import TYPE_CHECKING\nfrom __future__ import annotations\n", "from __future__ import annotations\nfrom typing import TYPE_CHECKING\n")

    with open(file, "w") as f:
        f.write(content)
