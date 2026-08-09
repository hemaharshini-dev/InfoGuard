from fastapi import APIRouter
from app.services.pipeline import run_benchmark

router = APIRouter()


@router.post("/benchmark")
async def benchmark() -> dict:
    report = await run_benchmark()
    return report.model_dump()
