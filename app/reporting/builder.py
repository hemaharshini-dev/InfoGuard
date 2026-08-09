"""Transforms EvaluationReport and single-run results into plain dicts for the PDF renderer."""
from datetime import datetime
from app.schemas.models import ComparatorResult, EvaluationReport


def build_report_data(report: EvaluationReport) -> dict:
    """Flatten an EvaluationReport into a serialisable dict for the benchmark PDF renderer."""
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
        b_issues = [{"type": i.issue_type.value, "description": i.description} for i in c.baseline_result.issues]
        l_issues = [{"type": i.issue_type.value, "description": i.description} for i in c.llm_result.issues]
        expected = [t.value for t in c.label.expected_issue_types]
        case_rows.append({
            "id": c.benchmark_id,
            "category": c.category.value,
            "expected": expected or ["none"],
            "baseline_issues": b_issues,
            "llm_issues": l_issues,
            "baseline_latency": c.baseline_result.latency_seconds,
            "llm_latency": c.llm_result.latency_seconds,
        })

    return {
        "mode": "benchmark",
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


def build_single_report_data(
    transcript: str,
    summary: str,
    baseline_result: ComparatorResult,
    llm_result: ComparatorResult,
    hybrid_result: ComparatorResult | None = None,
) -> dict:
    """Build a serialisable dict for the single-input PDF renderer."""
    b_issues = [{"type": i.issue_type.value, "description": i.description,
                 "transcript_excerpt": i.transcript_excerpt, "summary_excerpt": i.summary_excerpt}
                for i in baseline_result.issues]
    l_issues = [{"type": i.issue_type.value, "description": i.description,
                 "transcript_excerpt": i.transcript_excerpt, "summary_excerpt": i.summary_excerpt}
                for i in llm_result.issues]
    h_issues = [{"type": i.issue_type.value, "description": i.description,
                 "transcript_excerpt": i.transcript_excerpt, "summary_excerpt": i.summary_excerpt,
                 "confidence": i.confidence}
                for i in (hybrid_result.issues if hybrid_result else [])]

    # Verdict is driven by the hybrid result (most reliable)
    verdict_issues = h_issues if hybrid_result else l_issues
    all_types = {i["type"] for i in verdict_issues}
    verdict = "No issues found. The summary accurately reflects the transcript." if not all_types else (
        f"Found {len(verdict_issues)} issue(s) after cross-validation. "
        "The summary does not fully or accurately represent the transcript."
    )

    return {
        "mode": "single",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transcript": transcript,
        "summary": summary,
        "verdict": verdict,
        "hybrid_issues": h_issues,
        "baseline_issues": b_issues,
        "llm_issues": l_issues,
        "baseline_latency": baseline_result.latency_seconds,
        "llm_latency": llm_result.latency_seconds,
        "hybrid_latency": hybrid_result.latency_seconds if hybrid_result else 0.0,
        "issue_types_found": sorted(all_types) if all_types else [],
    }
