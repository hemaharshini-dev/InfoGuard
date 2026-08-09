"""Pydantic schemas shared across all layers of InfoGuard.

All comparators return ComparatorResult so the evaluation engine
can score any comparator without modification.
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class IssueType(str, Enum):
    """The four categories of mismatch InfoGuard can detect."""
    MISSING = "missing"        # fact in transcript, absent from summary
    INCORRECT = "incorrect"    # fact stated wrongly in summary
    CONFLICTING = "conflicting" # information that clashes without resolution
    EXTRA = "extra"            # summary adds facts not in transcript (hallucination)


class BenchmarkCategory(str, Enum):
    """The six categories used in the synthetic benchmark."""
    PERFECT_MATCH = "perfect_match"
    MISSING_FIELDS = "missing_fields"
    INCORRECT_VALUES = "incorrect_values"
    AMBIGUOUS = "ambiguous"
    SENSITIVE = "sensitive"
    EXTRA = "extra"


class ComparatorName(str, Enum):
    """Identifies which comparator produced a result."""
    BASELINE = "baseline"
    LLM = "llm"
    HYBRID = "hybrid"  # merged result combining baseline + LLM


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

class ComparisonInput(BaseModel):
    """A transcript/summary pair submitted for comparison."""
    transcript: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Issue — common output schema for both comparators
# ---------------------------------------------------------------------------

class Issue(BaseModel):
    """A single detected mismatch between transcript and summary."""
    issue_type: IssueType
    description: str
    transcript_excerpt: str | None = None  # relevant snippet from transcript
    summary_excerpt: str | None = None     # relevant snippet from summary
    confidence: float | None = None        # 0.0–1.0, LLM-provided; None for baseline


# ---------------------------------------------------------------------------
# Comparator output — same schema regardless of which comparator produced it
# ---------------------------------------------------------------------------

class ComparatorResult(BaseModel):
    """Uniform output returned by every comparator implementation."""
    comparator: ComparatorName
    issues: list[Issue] = Field(default_factory=list)
    latency_seconds: float = 0.0
    raw_output: Any = None  # stores LLM raw response for debugging


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

class BenchmarkLabel(BaseModel):
    """Ground truth for a benchmark case — which issue types should be detected."""
    expected_issue_types: list[IssueType] = Field(default_factory=list)
    notes: str = ""


class BenchmarkItem(BaseModel):
    """One benchmark case: input pair + ground truth label."""
    id: str
    category: BenchmarkCategory
    input: ComparisonInput
    label: BenchmarkLabel


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class IssueTypeMetrics(BaseModel):
    """Precision, recall, and F1 for a single issue type."""
    issue_type: IssueType
    precision: float
    recall: float
    f1: float


class ComparatorMetrics(BaseModel):
    """Aggregated evaluation metrics for one comparator across all benchmark cases."""
    comparator: ComparatorName
    overall_accuracy: float
    avg_latency_seconds: float
    issue_type_metrics: list[IssueTypeMetrics] = Field(default_factory=list)
    category_accuracy: dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class CaseResult(BaseModel):
    """Both comparators' outputs for a single benchmark case, alongside ground truth."""
    benchmark_id: str
    category: BenchmarkCategory
    baseline_result: ComparatorResult
    llm_result: ComparatorResult
    label: BenchmarkLabel


class EvaluationReport(BaseModel):
    """Full benchmark evaluation report covering all cases and both comparators."""
    total_cases: int
    baseline_metrics: ComparatorMetrics
    llm_metrics: ComparatorMetrics
    case_results: list[CaseResult] = Field(default_factory=list)
