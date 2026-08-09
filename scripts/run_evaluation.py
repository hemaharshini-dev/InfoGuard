from app.services.pipeline import run_benchmark_sync

print("Running full benchmark (baseline + LLM)...\n")
report = run_benchmark_sync()

for metrics in [report.baseline_metrics, report.llm_metrics]:
    print(f"=== {metrics.comparator.value.upper()} ===")
    print(f"  Overall accuracy   : {metrics.overall_accuracy:.0%}")
    print(f"  Avg latency        : {metrics.avg_latency_seconds:.4f}s")
    print(f"  Category accuracy  :")
    for cat, acc in metrics.category_accuracy.items():
        print(f"    {cat:<20} {acc:.0%}")
    print(f"  Issue-type metrics :")
    print(f"    {'type':<12} {'precision':>10} {'recall':>8} {'f1':>8}")
    for m in metrics.issue_type_metrics:
        print(f"    {m.issue_type.value:<12} {m.precision:>10.4f} {m.recall:>8.4f} {m.f1:>8.4f}")
    print()
