from app.evaluation.benchmark import load_benchmark
from app.evaluation.scorer import score, _case_correct
from app.comparators.baseline import BaselineComparator
from app.schemas.models import (
    BenchmarkItem, BenchmarkCategory, BenchmarkLabel,
    ComparisonInput, ComparatorName, ComparatorResult, IssueType, Issue,
)


def _make_result(issue_types: list[IssueType], comparator=ComparatorName.BASELINE) -> ComparatorResult:
    return ComparatorResult(
        comparator=comparator,
        issues=[Issue(issue_type=it, description="test") for it in issue_types],
        latency_seconds=0.01,
    )


def _make_item(expected: list[IssueType]) -> BenchmarkItem:
    return BenchmarkItem(
        id="test_001",
        category=BenchmarkCategory.MISSING_FIELDS,
        input=ComparisonInput(transcript="t", summary="s"),
        label=BenchmarkLabel(expected_issue_types=expected),
    )


def test_case_correct_when_expected_subset_of_detected():
    item = _make_item([IssueType.MISSING])
    result = _make_result([IssueType.MISSING, IssueType.EXTRA])
    assert _case_correct(result, item) is True


def test_case_incorrect_when_expected_not_detected():
    item = _make_item([IssueType.INCORRECT])
    result = _make_result([IssueType.MISSING])
    assert _case_correct(result, item) is False


def test_case_correct_when_no_issues_expected_and_none_detected():
    item = _make_item([])
    result = _make_result([])
    assert _case_correct(result, item) is True


def test_score_overall_accuracy_perfect():
    items = [_make_item([IssueType.MISSING])] * 3
    results = [_make_result([IssueType.MISSING])] * 3
    report = score(items, results, results)
    assert report.baseline_metrics.overall_accuracy == 1.0


def test_score_overall_accuracy_zero():
    items = [_make_item([IssueType.INCORRECT])] * 3
    results = [_make_result([])] * 3
    report = score(items, results, results)
    assert report.baseline_metrics.overall_accuracy == 0.0


def test_score_report_total_cases():
    items = load_benchmark()
    baseline = BaselineComparator()
    results = [baseline.compare(item.input) for item in items]
    report = score(items, results, results)
    assert report.total_cases == len(items)


def test_score_all_categories_present():
    items = load_benchmark()
    baseline = BaselineComparator()
    results = [baseline.compare(item.input) for item in items]
    report = score(items, results, results)
    assert len(report.baseline_metrics.category_accuracy) == 6


def test_issue_type_metrics_all_types_present():
    items = [_make_item([])] * 2
    results = [_make_result([])] * 2
    report = score(items, results, results)
    types = {m.issue_type for m in report.baseline_metrics.issue_type_metrics}
    assert types == set(IssueType)
