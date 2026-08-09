from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class IssueType(str, Enum):
    MISSING = "missing"
    INCORRECT = "incorrect"
    CONFLICTING = "conflicting"
    EXTRA = "extra"


class BenchmarkCategory(str, Enum):
    PERFECT_MATCH = "perfect_match"
    MISSING_FIELDS = "missing_fields"
    INCORRECT_VALUES = "incorrect_values"
    AMBIGUOUS = "ambiguous"
    SENSITIVE = "sensitive"
    EXTRA = "extra"


class ComparatorName(str, Enum):
    BASELINE = "baseline"
    LLM = "llm"


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

class ComparisonInput(BaseModel):
    transcript: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Issue — common output schema for both comparators
# ---------------------------------------------------------------------------

class Issue(BaseModel):
    issue_type: IssueType
    description: str
    transcript_excerpt: str | None = None
    summary_excerpt: str | None = None


# ---------------------------------------------------------------------------
# Comparator output — same schema regardless of which comparator produced it
# ---------------------------------------------------------------------------

class ComparatorResult(BaseModel):
    comparator: ComparatorName
    issues: list[Issue] = Field(default_factory=list)
    latency_seconds: float = 0.0
    raw_output: Any = None  # stores LLM raw response for debugging


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

class BenchmarkLabel(BaseModel):
    expected_issue_types: list[IssueType] = Field(default_factory=list)
    notes: str = ""


class BenchmarkItem(BaseModel):
    id: str
    category: BenchmarkCategory
    input: ComparisonInput
    label: BenchmarkLabel


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class IssueTypeMetrics(BaseModel):
    issue_type: IssueType
    precision: float
    recall: float
    f1: float


class ComparatorMetrics(BaseModel):
    comparator: ComparatorName
    overall_accuracy: float
    avg_latency_seconds: float
    issue_type_metrics: list[IssueTypeMetrics] = Field(default_factory=list)
    category_accuracy: dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class CaseResult(BaseModel):
    benchmark_id: str
    category: BenchmarkCategory
    baseline_result: ComparatorResult
    llm_result: ComparatorResult
    label: BenchmarkLabel


class EvaluationReport(BaseModel):
    total_cases: int
    baseline_metrics: ComparatorMetrics
    llm_metrics: ComparatorMetrics
    case_results: list[CaseResult] = Field(default_factory=list)
