import os
file = "pipeline/tests/test_deep_research_debug.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('engine = get_engine()', '')

with open(file, "w") as f:
    f.write(content)
