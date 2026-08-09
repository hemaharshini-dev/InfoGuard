from fastapi import APIRouter
from app.schemas.models import ComparisonInput, ComparatorResult
from app.services.pipeline import run_single

router = APIRouter()


class CompareResponse(ComparisonInput):
    pass


@router.post("/compare")
def compare(input: ComparisonInput) -> dict:
    results = run_single(input.transcript, input.summary)
    return {
        "baseline": results["baseline"].model_dump(),
        "llm": results["llm"].model_dump(),
    }
