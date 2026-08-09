from fastapi import APIRouter
from app.services.pipeline import run_benchmark

router = APIRouter()


@router.post("/benchmark")
def benchmark() -> dict:
    report = run_benchmark()
    return report.model_dump()
