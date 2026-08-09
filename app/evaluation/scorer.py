from collections import defaultdict
from app.schemas.models import (
    BenchmarkCategory,
    BenchmarkItem,
    CaseResult,
    ComparatorMetrics,
    ComparatorName,
    ComparatorResult,
    EvaluationReport,
    IssueType,
    IssueTypeMetrics,
)


def _precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return round(precision, 4), round(recall, 4), round(f1, 4)


def _case_correct(predicted: ComparatorResult, item: BenchmarkItem) -> bool:
    """A case is correct if every expected issue type appears at least once in predictions."""
    expected = set(item.label.expected_issue_types)
    detected = {i.issue_type for i in predicted.issues}
    return expected.issubset(detected)


def score(
    items: list[BenchmarkItem],
    baseline_results: list[ComparatorResult],
    llm_results: list[ComparatorResult],
) -> EvaluationReport:
    case_results: list[CaseResult] = []

    for item, b_res, l_res in zip(items, baseline_results, llm_results):
        case_results.append(CaseResult(
            benchmark_id=item.id,
            category=item.category,
            baseline_result=b_res,
            llm_result=l_res,
            label=item.label,
        ))

    baseline_metrics = _compute_metrics(ComparatorName.BASELINE, items, baseline_results)
    llm_metrics = _compute_metrics(ComparatorName.LLM, items, llm_results)

    return EvaluationReport(
        total_cases=len(items),
        baseline_metrics=baseline_metrics,
        llm_metrics=llm_metrics,
        case_results=case_results,
    )


def _compute_metrics(
    name: ComparatorName,
    items: list[BenchmarkItem],
    results: list[ComparatorResult],
) -> ComparatorMetrics:
    correct_total = 0
    latencies: list[float] = []

    # issue-type counters: tp, fp, fn per IssueType
    tp: dict[IssueType, int] = defaultdict(int)
    fp: dict[IssueType, int] = defaultdict(int)
    fn: dict[IssueType, int] = defaultdict(int)

    # category accuracy counters
    cat_correct: dict[BenchmarkCategory, int] = defaultdict(int)
    cat_total: dict[BenchmarkCategory, int] = defaultdict(int)

    for item, result in zip(items, results):
        latencies.append(result.latency_seconds)
        cat_total[item.category] += 1

        expected = set(item.label.expected_issue_types)
        detected = {i.issue_type for i in result.issues}

        # case-level correctness
        if expected.issubset(detected):
            correct_total += 1
            cat_correct[item.category] += 1

        # per issue-type tp/fp/fn
        for issue_type in IssueType:
            exp = issue_type in expected
            det = issue_type in detected
            if exp and det:
                tp[issue_type] += 1
            elif not exp and det:
                fp[issue_type] += 1
            elif exp and not det:
                fn[issue_type] += 1

    issue_type_metrics = [
        IssueTypeMetrics(
            issue_type=it,
            precision=_precision_recall_f1(tp[it], fp[it], fn[it])[0],
            recall=_precision_recall_f1(tp[it], fp[it], fn[it])[1],
            f1=_precision_recall_f1(tp[it], fp[it], fn[it])[2],
        )
        for it in IssueType
    ]

    category_accuracy = {
        cat.value: round(cat_correct[cat] / cat_total[cat], 4)
        for cat in cat_total
    }

    return ComparatorMetrics(
        comparator=name,
        overall_accuracy=round(correct_total / len(items), 4),
        avg_latency_seconds=round(sum(latencies) / len(latencies), 4),
        issue_type_metrics=issue_type_metrics,
        category_accuracy=category_accuracy,
    )
