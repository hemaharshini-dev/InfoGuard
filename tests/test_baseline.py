from app.comparators.baseline import BaselineComparator
from app.schemas.models import ComparisonInput, IssueType

comparator = BaselineComparator()


def test_perfect_match_no_issues():
    inp = ComparisonInput(
        transcript="The refund of $75 was issued on March 5th.",
        summary="A refund of $75 was issued on March 5th.",
    )
    result = comparator.compare(inp)
    issue_types = {i.issue_type for i in result.issues}
    assert IssueType.MISSING not in issue_types


def test_detects_missing_fact():
    inp = ComparisonInput(
        transcript="The order number is ORD-1234 and the refund is $50.",
        summary="A refund was issued.",
    )
    result = comparator.compare(inp)
    assert any(i.issue_type == IssueType.MISSING for i in result.issues)


def test_detects_extra_fact():
    inp = ComparisonInput(
        transcript="The meeting is on April 10th.",
        summary="The meeting is on April 10th. A follow-up is scheduled for May 1st.",
    )
    result = comparator.compare(inp)
    assert any(i.issue_type == IssueType.EXTRA for i in result.issues)


def test_detects_incorrect_value():
    inp = ComparisonInput(
        transcript="The customer is on the 500 Mbps plan.",
        summary="The customer is on the 200 Mbps plan.",
    )
    result = comparator.compare(inp)
    assert any(i.issue_type == IssueType.INCORRECT for i in result.issues)


def test_result_schema_has_comparator_name():
    from app.schemas.models import ComparatorName
    inp = ComparisonInput(transcript="Hello.", summary="Hello.")
    result = comparator.compare(inp)
    assert result.comparator == ComparatorName.BASELINE


def test_latency_is_positive():
    inp = ComparisonInput(transcript="Test transcript.", summary="Test summary.")
    result = comparator.compare(inp)
    assert result.latency_seconds >= 0.0
