import tempfile
from pathlib import Path
from app.reporting.builder import build_report_data, build_single_report_data
from app.reporting.pdf import render_pdf
from app.evaluation.scorer import score
from app.evaluation.benchmark import load_benchmark
from app.comparators.baseline import BaselineComparator
from app.schemas.models import ComparisonInput, ComparatorName, ComparatorResult, Issue, IssueType


def _make_report():
    items = load_benchmark()
    baseline = BaselineComparator()
    results = [baseline.compare(item.input) for item in items]
    return score(items, results, results)


def _make_single_data():
    inp = ComparisonInput(
        transcript="The refund of $75 was issued on March 5th to card ending 4821.",
        summary="A refund of $50 was issued.",
    )
    baseline_result = ComparatorResult(
        comparator=ComparatorName.BASELINE,
        issues=[Issue(issue_type=IssueType.INCORRECT, description="Wrong refund amount")],
        latency_seconds=0.01,
    )
    llm_result = ComparatorResult(
        comparator=ComparatorName.LLM,
        issues=[Issue(issue_type=IssueType.INCORRECT, description="Wrong refund amount", confidence=0.92)],
        latency_seconds=0.3,
    )
    hybrid_result = ComparatorResult(
        comparator=ComparatorName.HYBRID,
        issues=[Issue(issue_type=IssueType.INCORRECT, description="Wrong refund amount", confidence=0.96)],
        latency_seconds=0.31,
    )
    return build_single_report_data(inp.transcript, inp.summary, baseline_result, llm_result, hybrid_result)


# --- benchmark builder ---

def test_build_report_data_keys():
    data = build_report_data(_make_report())
    for key in ["generated_at", "total_cases", "baseline", "llm", "comparison_table", "case_rows"]:
        assert key in data


def test_build_report_mode_is_benchmark():
    data = build_report_data(_make_report())
    assert data["mode"] == "benchmark"


def test_build_report_total_cases():
    data = build_report_data(_make_report())
    assert data["total_cases"] == len(load_benchmark())


def test_build_report_case_rows_have_issue_descriptions():
    data = build_report_data(_make_report())
    for row in data["case_rows"]:
        assert "baseline_issues" in row
        assert "llm_issues" in row


def test_build_report_comparison_table_has_all_issue_types():
    from app.schemas.models import IssueType
    data = build_report_data(_make_report())
    types = {row["issue_type"] for row in data["comparison_table"]}
    assert types == {it.value for it in IssueType}


# --- single builder ---

def test_build_single_report_mode_is_single():
    data = _make_single_data()
    assert data["mode"] == "single"


def test_build_single_report_has_verdict():
    data = _make_single_data()
    assert "verdict" in data
    assert len(data["verdict"]) > 0


def test_build_single_report_has_issues():
    data = _make_single_data()
    assert "baseline_issues" in data
    assert "llm_issues" in data


def test_build_single_report_detects_issues_on_wrong_summary():
    data = _make_single_data()
    all_issues = data["baseline_issues"] + data["llm_issues"]
    assert len(all_issues) > 0


# --- PDF rendering ---

def test_render_benchmark_pdf_creates_file():
    data = build_report_data(_make_report())
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "bench.pdf"
        render_pdf(data, out)
        assert out.exists() and out.stat().st_size > 1000


def test_render_single_pdf_creates_file():
    data = _make_single_data()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "single.pdf"
        render_pdf(data, out)
        assert out.exists() and out.stat().st_size > 1000


def test_render_pdf_valid_pdf_header():
    data = _make_single_data()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.pdf"
        render_pdf(data, out)
        assert out.read_bytes()[:4] == b"%PDF"
