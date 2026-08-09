from collections import Counter
from app.evaluation.benchmark import load_benchmark

items = load_benchmark()
counts = Counter(item.category.value for item in items)
print(f"Total cases: {len(items)}")
for cat, n in sorted(counts.items()):
    print(f"  {cat}: {n}")
