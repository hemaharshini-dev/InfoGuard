import tempfile
from pathlib import Path
from app.reporting.builder import build_report_data
from app.reporting.pdf import render_pdf
from app.evaluation.scorer import score
from app.evaluation.benchmark import load_benchmark
from app.comparators.baseline import BaselineComparator


def _make_report():
    items = load_benchmark()
    baseline = BaselineComparator()
    results = [baseline.compare(item.input) for item in items]
    return score(items, results, results)


def test_build_report_data_keys():
    data = build_report_data(_make_report())
    for key in ["generated_at", "total_cases", "baseline", "llm", "comparison_table", "case_rows"]:
        assert key in data


def test_build_report_total_cases():
    data = build_report_data(_make_report())
    assert data["total_cases"] == len(load_benchmark())


def test_build_report_comparison_table_has_all_issue_types():
    from app.schemas.models import IssueType
    data = build_report_data(_make_report())
    types = {row["issue_type"] for row in data["comparison_table"]}
    assert types == {it.value for it in IssueType}


def test_build_report_case_rows_count():
    data = build_report_data(_make_report())
    assert len(data["case_rows"]) == len(load_benchmark())


def test_render_pdf_creates_file():
    data = build_report_data(_make_report())
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test_report.pdf"
        render_pdf(data, out)
        assert out.exists()
        assert out.stat().st_size > 1000


def test_render_pdf_starts_with_pdf_header():
    data = build_report_data(_make_report())
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test_report.pdf"
        render_pdf(data, out)
        assert out.read_bytes()[:4] == b"%PDF"
