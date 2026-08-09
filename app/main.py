from fastapi import FastAPI
from app.api import health, evaluate, benchmark, report

app = FastAPI(
    title="InfoGuard",
    description="Transcript vs Summary evaluation framework",
    version="0.1.0",
)

app.include_router(health.router, tags=["health"])
app.include_router(evaluate.router, tags=["evaluate"])
app.include_router(benchmark.router, tags=["benchmark"])
app.include_router(report.router, tags=["report"])
