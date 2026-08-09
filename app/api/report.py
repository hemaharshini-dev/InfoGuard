from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.services.pipeline import run_benchmark
from app.reporting.builder import build_report_data
from app.reporting.pdf import render_pdf

router = APIRouter()

_REPORT_PATH = Path("reports") / "evaluation_report.pdf"


@router.post("/report")
def generate_report() -> FileResponse:
    report = run_benchmark()
    data = build_report_data(report)
    render_pdf(data, _REPORT_PATH)
    return FileResponse(
        path=str(_REPORT_PATH),
        media_type="application/pdf",
        filename="evaluation_report.pdf",
    )
