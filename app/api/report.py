from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.schemas.models import ComparisonInput
from app.services.pipeline import run_benchmark, run_single
from app.reporting.builder import build_report_data, build_single_report_data
from app.reporting.pdf import render_pdf

router = APIRouter()

_BENCHMARK_REPORT = Path("reports") / "evaluation_report.pdf"
_SINGLE_REPORT    = Path("reports") / "comparison_report.pdf"


@router.post("/report")
def generate_benchmark_report() -> FileResponse:
    report = run_benchmark()
    data = build_report_data(report)
    render_pdf(data, _BENCHMARK_REPORT)
    return FileResponse(
        path=str(_BENCHMARK_REPORT),
        media_type="application/pdf",
        filename="evaluation_report.pdf",
    )


@router.post("/report/compare")
def generate_single_report(input: ComparisonInput) -> FileResponse:
    results = run_single(input.transcript, input.summary)
    data = build_single_report_data(
        transcript=input.transcript,
        summary=input.summary,
        baseline_result=results["baseline"],
        llm_result=results["llm"],
    )
    render_pdf(data, _SINGLE_REPORT)
    return FileResponse(
        path=str(_SINGLE_REPORT),
        media_type="application/pdf",
        filename="comparison_report.pdf",
    )
