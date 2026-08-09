from app.evaluation.benchmark import load_benchmark
from app.comparators.llm import LLMComparator

comparator = LLMComparator()

for item in load_benchmark():
    result = comparator.compare(item.input)
    issue_types = [i.issue_type.value for i in result.issues]
    expected = [t.value for t in item.label.expected_issue_types]
    status = "PASS" if set(issue_types) >= set(expected) else "FAIL"
    print(f"[{status}] {item.id} ({item.category.value})")
    print(f"     expected : {expected}")
    print(f"     detected : {issue_types}")
    print(f"     latency  : {result.latency_seconds}s")
