
## 2026-03-03 - [Ordered Deduplication Optimization]
**Learning:** Manual loop-and-set approaches for deduplication with order preservation are less efficient and idiomatic than `list(dict.fromkeys(sequence))`. The latter is completely implemented in C.
**Action:** Always favor `list(dict.fromkeys(sequence))` for performance and conciseness when deduplicating sequences of hashable items where order matters in Python 3.7+.
