from datetime import datetime
from app.schemas.models import EvaluationReport


def build_report_data(report: EvaluationReport) -> dict:
    b = report.baseline_metrics
    l = report.llm_metrics

    comparison_table = []
    for b_m, l_m in zip(b.issue_type_metrics, l.issue_type_metrics):
        comparison_table.append({
            "issue_type": b_m.issue_type.value,
            "baseline_precision": b_m.precision,
            "baseline_recall": b_m.recall,
            "baseline_f1": b_m.f1,
            "llm_precision": l_m.precision,
            "llm_recall": l_m.recall,
            "llm_f1": l_m.f1,
        })

    case_rows = []
    for c in report.case_results:
        b_types = list({i.issue_type.value for i in c.baseline_result.issues})
        l_types = list({i.issue_type.value for i in c.llm_result.issues})
        expected = [t.value for t in c.label.expected_issue_types]
        case_rows.append({
            "id": c.benchmark_id,
            "category": c.category.value,
            "expected": expected or ["none"],
            "baseline": b_types or ["none"],
            "llm": l_types or ["none"],
            "baseline_latency": c.baseline_result.latency_seconds,
            "llm_latency": c.llm_result.latency_seconds,
        })

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_cases": report.total_cases,
        "baseline": {
            "overall_accuracy": b.overall_accuracy,
            "avg_latency": b.avg_latency_seconds,
            "category_accuracy": b.category_accuracy,
        },
        "llm": {
            "overall_accuracy": l.overall_accuracy,
            "avg_latency": l.avg_latency_seconds,
            "category_accuracy": l.category_accuracy,
        },
        "comparison_table": comparison_table,
        "case_rows": case_rows,
    }
