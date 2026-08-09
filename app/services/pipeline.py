"""Pipeline service — orchestrates both comparators for benchmark and single-input runs.

The benchmark pipeline runs all 12 cases concurrently using ThreadPoolExecutor
so that LLM API calls overlap in time. On a cold run this reduces wall-clock
time from ~5s (sequential) to ~1s (concurrent).

run_benchmark()      — async, used by FastAPI route handlers
run_benchmark_sync() — sync wrapper, used by CLI scripts
run_single()         — sync, used by /compare and /report/compare
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.comparators.baseline import BaselineComparator
from app.comparators.hybrid import HybridComparator
from app.comparators.llm import LLMComparator
from app.evaluation.benchmark import load_benchmark
from app.evaluation.scorer import score
from app.schemas.models import BenchmarkItem, ComparisonInput, ComparatorResult, EvaluationReport


def _run_case(item: BenchmarkItem) -> tuple[ComparatorResult, ComparatorResult]:
    """Run both comparators on a single benchmark item. Called in a thread."""
    baseline = BaselineComparator()
    llm = LLMComparator()
    return baseline.compare(item.input), llm.compare(item.input)


async def run_benchmark() -> EvaluationReport:
    """Run both comparators over all benchmark cases concurrently and return a scored EvaluationReport."""
    items = load_benchmark()
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        futures = [loop.run_in_executor(pool, _run_case, item) for item in items]
        pairs = await asyncio.gather(*futures)
    baseline_results = [p[0] for p in pairs]
    llm_results = [p[1] for p in pairs]
    return score(items, baseline_results, llm_results)


def run_benchmark_sync() -> EvaluationReport:
    """Synchronous wrapper around run_benchmark for scripts that don't run an event loop."""
    return asyncio.run(run_benchmark())


def run_single(transcript: str, summary: str) -> dict:
    """Run all three comparators on a single transcript/summary pair and return their results."""
    input_ = ComparisonInput(transcript=transcript, summary=summary)
    baseline = BaselineComparator()
    llm = LLMComparator()
    hybrid = HybridComparator()
    return {
        "baseline": baseline.compare(input_),
        "llm": llm.compare(input_),
        "hybrid": hybrid.compare(input_),
    }
