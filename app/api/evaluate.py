"""POST /compare endpoint.

Runs both comparators on a transcript/summary pair and returns:
- baseline: rule-based result with issues
- llm: LLM result with issues and per-issue confidence scores
- agreement: summary of whether both methods found the same issue types,
  which types they agreed on, and where they diverged
"""
from fastapi import APIRouter
from app.schemas.models import ComparisonInput
from app.services.pipeline import run_single

router = APIRouter()


@router.post("/compare")
def compare(input: ComparisonInput) -> dict:
    """Compare transcript vs summary using both comparators and return results with agreement summary."""
    results = run_single(input.transcript, input.summary)
    baseline = results["baseline"]
    llm = results["llm"]

    baseline_types = {i.issue_type for i in baseline.issues}
    llm_types = {i.issue_type for i in llm.issues}

    # agreement: both methods found the same set of issue types
    agreement = baseline_types == llm_types
    # overlap: issue types detected by both
    agreed_types = sorted(t.value for t in baseline_types & llm_types)
    # only_baseline / only_llm: divergences between the two methods
    only_baseline = sorted(t.value for t in baseline_types - llm_types)
    only_llm = sorted(t.value for t in llm_types - baseline_types)

    return {
        "baseline": baseline.model_dump(),
        "llm": llm.model_dump(),
        "agreement": {
            "methods_agree": agreement,
            "agreed_issue_types": agreed_types,
            "only_in_baseline": only_baseline,
            "only_in_llm": only_llm,
        },
    }
