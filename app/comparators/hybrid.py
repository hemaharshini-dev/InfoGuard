"""Hybrid comparator — merges baseline and LLM results into a single superior output.

Combination rules applied in order:

1. CONFIRMED issues — LLM issue whose type is also flagged by the baseline.
   Confidence is boosted by 10% (capped at 1.0) because two independent methods agree.

2. LLM-ONLY issues — LLM flagged it but baseline did not.
   Kept as-is. The LLM catches semantic issues the baseline cannot see.

3. BASELINE-ONLY issues — baseline flagged it but LLM did not.
   Suppressed. Without LLM confirmation these are likely false positives
   (baseline noise from token-level matching).

The result is a ComparatorResult with comparator=HYBRID containing only
confirmed and LLM-only issues, with adjusted confidence scores.
"""
import time
from app.comparators.base import BaseComparator
from app.schemas.models import (
    ComparisonInput,
    ComparatorResult,
    ComparatorName,
    Issue,
)
from app.comparators.baseline import BaselineComparator
from app.comparators.llm import LLMComparator

# How much to boost confidence when baseline confirms an LLM issue
_CONFIRMATION_BOOST = 0.10


class HybridComparator(BaseComparator):
    """Runs baseline and LLM comparators then merges their outputs.

    - Confirmed issues (both agree): confidence boosted by 10%
    - LLM-only issues: kept unchanged
    - Baseline-only issues: suppressed as likely false positives
    """

    def __init__(self) -> None:
        self._baseline = BaselineComparator()
        self._llm = LLMComparator()

    def compare(self, input: ComparisonInput) -> ComparatorResult:
        """Run both comparators and return a merged, deduplicated result."""
        start = time.perf_counter()

        baseline_result = self._baseline.compare(input)
        llm_result = self._llm.compare(input)

        # Set of issue types the baseline detected — used for confirmation check
        baseline_types = {i.issue_type for i in baseline_result.issues}

        merged: list[Issue] = []
        for llm_issue in llm_result.issues:
            if llm_issue.issue_type in baseline_types:
                # Confirmed by baseline — boost confidence
                current_conf = llm_issue.confidence if llm_issue.confidence is not None else 0.7
                boosted = round(min(current_conf + _CONFIRMATION_BOOST, 1.0), 4)
                merged.append(Issue(
                    issue_type=llm_issue.issue_type,
                    description=llm_issue.description,
                    transcript_excerpt=llm_issue.transcript_excerpt,
                    summary_excerpt=llm_issue.summary_excerpt,
                    confidence=boosted,
                ))
            else:
                # LLM-only — keep as-is, baseline couldn't see it
                merged.append(llm_issue)

        # Baseline-only issues are intentionally dropped (noise suppression)

        latency = time.perf_counter() - start
        return ComparatorResult(
            comparator=ComparatorName.HYBRID,
            issues=merged,
            latency_seconds=round(latency, 4),
        )
