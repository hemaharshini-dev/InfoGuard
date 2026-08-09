"""Tests for the HybridComparator combination logic."""
from unittest.mock import patch
from app.comparators.hybrid import HybridComparator
from app.schemas.models import (
    ComparisonInput,
    ComparatorName,
    ComparatorResult,
    Issue,
    IssueType,
)

_INPUT = ComparisonInput(
    transcript="Agent confirmed a refund of $75 within 5 business days.",
    summary="Agent confirmed a refund of $50 within 3 business days.",
)


def _baseline_result(issues):
    return ComparatorResult(comparator=ComparatorName.BASELINE, issues=issues, latency_seconds=0.001)


def _llm_result(issues):
    return ComparatorResult(comparator=ComparatorName.LLM, issues=issues, latency_seconds=0.3)


# ---------------------------------------------------------------------------
# Confirmed issues — both agree → confidence boosted
# ---------------------------------------------------------------------------

@patch("app.comparators.hybrid.LLMComparator.compare")
@patch("app.comparators.hybrid.BaselineComparator.compare")
def test_confirmed_issue_boosts_confidence(mock_baseline, mock_llm):
    mock_baseline.return_value = _baseline_result([
        Issue(issue_type=IssueType.INCORRECT, description="baseline flagged incorrect")
    ])
    mock_llm.return_value = _llm_result([
        Issue(issue_type=IssueType.INCORRECT, description="llm flagged incorrect", confidence=0.8)
    ])
    result = HybridComparator().compare(_INPUT)
    assert len(result.issues) == 1
    assert result.issues[0].confidence == 0.9  # 0.8 + 0.10 boost


@patch("app.comparators.hybrid.LLMComparator.compare")
@patch("app.comparators.hybrid.BaselineComparator.compare")
def test_confidence_boost_capped_at_1(mock_baseline, mock_llm):
    mock_baseline.return_value = _baseline_result([
        Issue(issue_type=IssueType.MISSING, description="baseline missing")
    ])
    mock_llm.return_value = _llm_result([
        Issue(issue_type=IssueType.MISSING, description="llm missing", confidence=0.95)
    ])
    result = HybridComparator().compare(_INPUT)
    assert result.issues[0].confidence == 1.0  # capped


# ---------------------------------------------------------------------------
# LLM-only issues — kept as-is
# ---------------------------------------------------------------------------

@patch("app.comparators.hybrid.LLMComparator.compare")
@patch("app.comparators.hybrid.BaselineComparator.compare")
def test_llm_only_issue_is_kept(mock_baseline, mock_llm):
    mock_baseline.return_value = _baseline_result([])  # baseline found nothing
    mock_llm.return_value = _llm_result([
        Issue(issue_type=IssueType.EXTRA, description="hallucination", confidence=0.75)
    ])
    result = HybridComparator().compare(_INPUT)
    assert len(result.issues) == 1
    assert result.issues[0].confidence == 0.75  # unchanged


# ---------------------------------------------------------------------------
# Baseline-only issues — suppressed
# ---------------------------------------------------------------------------

@patch("app.comparators.hybrid.LLMComparator.compare")
@patch("app.comparators.hybrid.BaselineComparator.compare")
def test_baseline_only_issue_is_suppressed(mock_baseline, mock_llm):
    mock_baseline.return_value = _baseline_result([
        Issue(issue_type=IssueType.MISSING, description="baseline noise")
    ])
    mock_llm.return_value = _llm_result([])  # LLM found nothing
    result = HybridComparator().compare(_INPUT)
    assert len(result.issues) == 0  # baseline-only suppressed


# ---------------------------------------------------------------------------
# Schema and metadata
# ---------------------------------------------------------------------------

@patch("app.comparators.hybrid.LLMComparator.compare")
@patch("app.comparators.hybrid.BaselineComparator.compare")
def test_hybrid_comparator_name(mock_baseline, mock_llm):
    mock_baseline.return_value = _baseline_result([])
    mock_llm.return_value = _llm_result([])
    result = HybridComparator().compare(_INPUT)
    assert result.comparator == ComparatorName.HYBRID


@patch("app.comparators.hybrid.LLMComparator.compare")
@patch("app.comparators.hybrid.BaselineComparator.compare")
def test_hybrid_latency_is_positive(mock_baseline, mock_llm):
    mock_baseline.return_value = _baseline_result([])
    mock_llm.return_value = _llm_result([])
    result = HybridComparator().compare(_INPUT)
    assert result.latency_seconds >= 0


# ---------------------------------------------------------------------------
# /compare endpoint includes hybrid field
# ---------------------------------------------------------------------------

def test_compare_endpoint_includes_hybrid():
    from unittest.mock import MagicMock
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)

    mock_result = ComparatorResult(
        comparator=ComparatorName.LLM, issues=[], latency_seconds=0.3
    )
    with patch("app.comparators.llm.LLMComparator.compare", return_value=mock_result):
        r = client.post("/compare", json={
            "transcript": "Agent confirmed refund of $75 in 5 days.",
            "summary": "Agent confirmed refund of $75 in 5 days.",
        })
    assert r.status_code == 200
    assert "hybrid" in r.json()
    assert "comparator" in r.json()["hybrid"]
