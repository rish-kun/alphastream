import os
file = "pipeline/tests/test_deep_research_debug.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('                engine = get_engine()\n                with engine.connect() as conn:', '                with mock_engine.return_value.connect() as conn:')

with open(file, "w") as f:
    f.write(content)
