"""Loads benchmark cases from data/benchmark/cases.json."""
import json
from pathlib import Path
from app.schemas.models import BenchmarkItem

BENCHMARK_PATH = Path(__file__).parent.parent.parent / "data" / "benchmark" / "cases.json"


def load_benchmark() -> list[BenchmarkItem]:
    """Read and validate all benchmark cases from disk."""
    raw = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    return [BenchmarkItem.model_validate(item) for item in raw]
