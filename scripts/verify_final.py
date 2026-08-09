from app.schemas.models import ComparisonInput, ComparatorResult, EvaluationReport
from app.core.config import settings
from app.comparators.baseline import BaselineComparator
from app.comparators.llm import LLMComparator
from app.evaluation.benchmark import load_benchmark
from app.evaluation.scorer import score
from app.reporting.builder import build_report_data, build_single_report_data
from app.reporting.pdf import render_pdf
from app.services.pipeline import run_single
from app.main import app

print("All imports OK")
print(f"Model: {settings.groq_model}")
print(f"Benchmark cases: {len(load_benchmark())}")
