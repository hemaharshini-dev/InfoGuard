import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

_TRANSCRIPT = (
    "Agent: Can I get your order number?\n"
    "Customer: It is ORD-9910. I was charged $200 but my plan is $100 per month.\n"
    "Agent: I see the error. A refund of $100 will be issued within 3 business days."
)
_SUMMARY_CORRECT = (
    "Customer reported a billing error on order ORD-9910. "
    "They were charged $200 instead of $100. "
    "Agent confirmed a refund of $100 within 3 business days."
)
_SUMMARY_WRONG = (
    "Customer reported a billing error. "
    "Agent confirmed a refund of $50 within 5 business days."
)


def test_health_returns_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_includes_model():
    r = client.get("/health")
    assert "model" in r.json()


def test_compare_returns_baseline_and_llm():
    r = client.post("/compare", json={"transcript": _TRANSCRIPT, "summary": _SUMMARY_CORRECT})
    assert r.status_code == 200
    body = r.json()
    assert "baseline" in body
    assert "llm" in body


def test_compare_baseline_has_issues_schema():
    r = client.post("/compare", json={"transcript": _TRANSCRIPT, "summary": _SUMMARY_CORRECT})
    baseline = r.json()["baseline"]
    assert "issues" in baseline
    assert "latency_seconds" in baseline
    assert "comparator" in baseline


def test_compare_detects_incorrect_on_wrong_summary():
    r = client.post("/compare", json={"transcript": _TRANSCRIPT, "summary": _SUMMARY_WRONG})
    assert r.status_code == 200
    baseline_types = [i["issue_type"] for i in r.json()["baseline"]["issues"]]
    llm_types = [i["issue_type"] for i in r.json()["llm"]["issues"]]
    assert len(baseline_types) > 0 or len(llm_types) > 0


def test_compare_rejects_empty_transcript():
    r = client.post("/compare", json={"transcript": "", "summary": "some summary"})
    assert r.status_code == 422


def test_compare_rejects_empty_summary():
    r = client.post("/compare", json={"transcript": "some transcript", "summary": ""})
    assert r.status_code == 422


def test_benchmark_returns_report_structure():
    r = client.post("/benchmark")
    assert r.status_code == 200
    body = r.json()
    assert "total_cases" in body
    assert "baseline_metrics" in body
    assert "llm_metrics" in body
    assert "case_results" in body


def test_benchmark_total_cases_is_12():
    r = client.post("/benchmark")
    assert r.json()["total_cases"] == 12


def test_report_returns_pdf():
    r = client.post("/report")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"
