"""POST /compare endpoint.

Runs all three comparators on a transcript/summary pair and returns:
- baseline: rule-based result
- llm: LLM result with per-issue confidence scores
- hybrid: merged result — confirmed issues boosted, baseline-only noise suppressed
- agreement: summary of whether baseline and LLM found the same issue types
"""
from fastapi import APIRouter
from app.schemas.models import ComparisonInput
from app.services.pipeline import run_single

router = APIRouter()


@router.post("/compare")
def compare(input: ComparisonInput) -> dict:
    """Compare transcript vs summary using all three comparators and return results with agreement summary."""
    results = run_single(input.transcript, input.summary)
    baseline = results["baseline"]
    llm = results["llm"]
    hybrid = results["hybrid"]

    baseline_types = {i.issue_type for i in baseline.issues}
    llm_types = {i.issue_type for i in llm.issues}

    # agreement: both methods found the same set of issue types
    agreement = baseline_types == llm_types
    agreed_types   = sorted(t.value for t in baseline_types & llm_types)
    only_baseline  = sorted(t.value for t in baseline_types - llm_types)
    only_llm       = sorted(t.value for t in llm_types - baseline_types)

    return {
        "baseline": baseline.model_dump(),
        "llm": llm.model_dump(),
        "hybrid": hybrid.model_dump(),
        "agreement": {
            "methods_agree": agreement,
            "agreed_issue_types": agreed_types,
            "only_in_baseline": only_baseline,
            "only_in_llm": only_llm,
        },
    }
