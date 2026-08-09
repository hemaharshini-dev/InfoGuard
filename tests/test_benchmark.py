from app.evaluation.benchmark import load_benchmark
from app.schemas.models import BenchmarkCategory


def test_benchmark_loads_without_error():
    items = load_benchmark()
    assert len(items) > 0


def test_all_categories_represented():
    items = load_benchmark()
    categories = {item.category for item in items}
    assert categories == set(BenchmarkCategory)


def test_all_items_have_valid_input():
    for item in load_benchmark():
        assert item.input.transcript.strip()
        assert item.input.summary.strip()


def test_all_items_have_unique_ids():
    items = load_benchmark()
    ids = [item.id for item in items]
    assert len(ids) == len(set(ids))


def test_labels_contain_valid_issue_types():
    from app.schemas.models import IssueType
    valid = set(IssueType)
    for item in load_benchmark():
        for it in item.label.expected_issue_types:
            assert it in valid
