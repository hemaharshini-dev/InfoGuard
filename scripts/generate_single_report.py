from pathlib import Path
from app.services.pipeline import run_single
from app.reporting.builder import build_single_report_data
from app.reporting.pdf import render_pdf

transcript = (
    "Agent: Thank you for calling. Can I get your name?\n"
    "Customer: Sure, I am Sarah. I was charged $150 on April 3rd but my plan is only $75 per month.\n"
    "Agent: I can see the error. You were billed twice due to a system glitch. "
    "I will issue a refund of $75 to your card ending in 9921 within 5 business days.\n"
    "Customer: Thank you so much."
)
summary = (
    "Customer Sarah reported a billing error. "
    "Agent confirmed a refund of $75 within 3 business days."
)

print("Running comparators...")
results = run_single(transcript, summary)

print("Building report data...")
data = build_single_report_data(transcript, summary, results["baseline"], results["llm"])

out = Path("reports") / "comparison_report.pdf"
print(f"Rendering PDF -> {out}")
render_pdf(data, out)
print("Done.")
