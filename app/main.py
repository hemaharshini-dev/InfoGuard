"""FastAPI application entrypoint — registers all route handlers and serves the UI."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api import health, evaluate, benchmark, report

_UI_DIR = Path(__file__).parent / "ui"

app = FastAPI(
    title="InfoGuard",
    description="Transcript vs Summary evaluation framework",
    version="0.1.0",
)

app.include_router(health.router, tags=["health"])
app.include_router(evaluate.router, tags=["evaluate"])
app.include_router(benchmark.router, tags=["benchmark"])
app.include_router(report.router, tags=["report"])

# Serve the UI — must be registered after API routes
app.mount("/ui", StaticFiles(directory=_UI_DIR, html=True), name="ui")


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    """Redirect root to the UI."""
    return FileResponse(_UI_DIR / "index.html")
