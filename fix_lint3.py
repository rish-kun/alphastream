import os
for file in ["backend/app/models/news.py", "backend/app/models/portfolio.py", "backend/app/models/stock.py"]:
    with open(file, "r") as f:
        lines = f.readlines()

    if "from typing import TYPE_CHECKING" not in "".join(lines):
        lines.insert(0, "from typing import TYPE_CHECKING\n")
        with open(file, "w") as f:
            f.writelines(lines)
