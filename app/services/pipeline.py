"""Pipeline service — orchestrates both comparators for benchmark and single-input runs."""
from app.comparators.baseline import BaselineComparator
from app.comparators.llm import LLMComparator
from app.evaluation.benchmark import load_benchmark
from app.evaluation.scorer import score
from app.schemas.models import ComparisonInput, ComparatorResult, EvaluationReport


def run_benchmark() -> EvaluationReport:
    """Run both comparators over all benchmark cases and return a scored EvaluationReport."""
    items = load_benchmark()
    baseline = BaselineComparator()
    llm = LLMComparator()

    baseline_results: list[ComparatorResult] = []
    llm_results: list[ComparatorResult] = []

    for item in items:
        baseline_results.append(baseline.compare(item.input))
        llm_results.append(llm.compare(item.input))

    return score(items, baseline_results, llm_results)


def run_single(transcript: str, summary: str) -> dict:
    """Run both comparators on a single transcript/summary pair and return their results."""
    input_ = ComparisonInput(transcript=transcript, summary=summary)
    baseline = BaselineComparator()
    llm = LLMComparator()
    return {
        "baseline": baseline.compare(input_),
        "llm": llm.compare(input_),
    }
