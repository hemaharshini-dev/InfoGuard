from pathlib import Path
from app.services.pipeline import run_benchmark
from app.reporting.builder import build_report_data
from app.reporting.pdf import render_pdf

print("Running benchmark...")
report = run_benchmark()

print("Building report data...")
data = build_report_data(report)

output = Path("reports") / "evaluation_report.pdf"
print(f"Rendering PDF -> {output}")
render_pdf(data, output)
print("Done.")
