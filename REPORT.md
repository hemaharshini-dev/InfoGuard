# InfoGuard — Technical Report

## 1. Problem Statement and Goal

The same information can exist in different formats. When a customer service transcript is summarised, the summary may omit facts, state them incorrectly, or introduce information that was never said. These mismatches are hard to catch manually at scale.

InfoGuard is an evaluation framework that automatically compares a transcript against its summary and identifies every factual discrepancy. The system detects four issue types: missing information, incorrect information, conflicting information, and extra information (hallucinations). It produces a structured evaluation report for both individual comparisons and batch benchmark runs, and a hybrid merged result is used for the single-comparison PDF when available.

---

## 2. Chosen Use Case

**Transcript vs Summary**

A transcript is the verbatim record of a conversation. A summary is a shorter version of it. The system treats the transcript as the ground truth and verifies whether the summary faithfully represents it.

This use case was chosen because:

- It directly matches the "same information, different formats" framing
- It naturally produces all four issue types
- Synthetic benchmark cases are easy to construct and label
- It is easy to explain and demonstrate

---

## 3. System Architecture

InfoGuard is an API-first application built with FastAPI. The pipeline has five layers:

```
Input (transcript + summary)
        ↓
Normalization — cleans and segments text into comparable units
        ↓
Comparators — Baseline and LLM run in parallel on the same input, then a hybrid result merges their outputs for the comparison report
        ↓
Evaluation — scores predictions against benchmark ground truth
        ↓
Reporting — builds structured report and renders to PDF
```

All comparators implement the same `BaseComparator` interface and return a `ComparatorResult` with a list of `Issue` objects. This uniform schema means the evaluation engine can score any comparator without modification.

---

## 4. Comparison Approaches

### Approach 1 — Rule-Based Baseline

The baseline extracts facts from both texts using regex patterns covering numbers, dollar amounts, dates, identifiers (e.g. ORD-6612), technical specs (e.g. 500 Mbps), IP addresses, and email addresses. It then:

- Flags facts in the transcript that are absent from the summary as **missing**
- Flags facts in the summary that are absent from the transcript as **extra**
- Finds sentence pairs with high token overlap and flags differing fact values as **incorrect**

**Advantages:** Free, runs locally, fully deterministic, ~1ms per case, no API dependency.

**Limitations:** Cannot understand meaning or paraphrasing. Cannot detect semantic equivalence (e.g. "$75" vs "seventy-five dollars").

### Approach 2 — LLM Comparator (Groq)

The LLM comparator sends the transcript and summary to `llama-3.3-70b-versatile` via the Groq API with a structured system prompt. The model is instructed to return a JSON array of issues, each with an issue type, description, and relevant excerpts. Temperature is set to 0.0 for deterministic output.

**Advantages:** Understands context, paraphrasing, and meaning-level differences. Produces human-readable descriptions. Fewer false alarms. Handles ambiguous cases better.

**Limitations:** ~300–800ms per case. Requires internet and a paid API key. Subject to rate limits and model deprecation. Non-deterministic across model updates.

### Hybrid Output — Merged Comparison View

The hybrid result combines baseline and LLM findings into a single merged output for the user-facing comparison report. It keeps confirmed issues and reduces obvious baseline-only noise, so the PDF can present one recommended view alongside the individual comparator outputs.

**Advantages:** Better user-facing summary, combines rule-based precision with LLM reasoning, reduces duplicate or noisy flags.

**Limitations:** It still depends on the quality of the underlying comparators.

---

## 5. Benchmark Design

The synthetic benchmark contains 12 cases across 6 categories, 2 cases per category:

| Category         | What it tests                                         |
| ---------------- | ----------------------------------------------------- |
| Perfect Match    | Summary fully agrees — no issues should be flagged    |
| Missing Fields   | Summary omits key facts from the transcript           |
| Incorrect Values | Summary states a fact that contradicts the transcript |
| Ambiguous        | Transcript is vague — hard to verify the summary      |
| Sensitive        | Transcript contains PII — tests appropriate handling  |
| Extra            | Summary adds information never in the transcript      |

Each case has a transcript, summary, and a ground truth label listing the expected issue types. Labels were written manually and are human-auditable. Cases are stored in `data/benchmark/cases.json`.

---

## 6. Evaluation Metrics and Results

Both comparators achieved **100% accuracy** on the benchmark — meaning in every case, the expected issue type was present in the detected issues. The hybrid output is not benchmarked separately; it is used in the single-comparison report to present a merged view.

| Metric                | Rule-Based (Baseline) | AI Analysis (Groq) |
| --------------------- | --------------------- | ------------------ |
| Overall Accuracy      | 100%                  | 100%               |
| Avg Latency           | ~1 ms                 | ~420 ms            |
| Missing — Precision   | 0.38                  | 0.50               |
| Missing — Recall      | 1.00                  | 1.00               |
| Incorrect — Precision | 1.00                  | 0.67               |
| Incorrect — Recall    | 1.00                  | 1.00               |
| Extra — Precision     | 0.50                  | 1.00               |
| Extra — Recall        | 1.00                  | 1.00               |

**Key observations:**

- Both methods achieve perfect recall — they never miss a real issue
- The LLM has significantly better precision on `extra` (1.00 vs 0.50) — it does not generate false hallucination alarms
- The baseline has lower precision on `missing` (0.38) because it flags individual tokens separately
- The LLM is ~420x slower per case

> Note: baseline precision on `missing` has since improved due to sentence-level fact grouping (Enhancement 2). The figures above reflect the original implementation.

---

## 7. Trade-offs

| Dimension              | Rule-Based Baseline        | LLM Comparator                   |
| ---------------------- | -------------------------- | -------------------------------- |
| Speed                  | ~1ms                       | ~300–800ms                       |
| Cost                   | Free                       | Groq API (free tier available)   |
| Accuracy               | High recall, low precision | High recall, high precision      |
| Determinism            | Fully deterministic        | Deterministic at temperature=0.0 |
| Semantic understanding | None                       | Strong                           |
| Dependency             | None                       | Internet + API key               |

The baseline is the right choice when speed and zero-cost operation matter and inputs are structured. The LLM comparator is the right choice when accuracy and human-readable explanations matter more than latency.

---

## 8. Strengths, Limitations, and Next Steps

### Strengths

- Clean layered architecture — comparators, evaluation, and reporting are fully decoupled
- Uniform schema means any new comparator can be added without touching the evaluator
- Both approaches are well-contrasted — they differ in speed, cost, and behaviour
- PDF reports are human-readable with plain-English explanations
- Built-in web UI served directly by FastAPI — no separate frontend server needed
- LLM responses cached to disk — identical inputs never hit the API twice
- Benchmark runs all 12 cases concurrently — cold run completes in ~1s
- Per-issue confidence scores from the LLM help users prioritise which flags to act on
- Agreement summary on `/compare` shows at a glance whether both methods concur
- Hybrid comparison view in the PDF presents the merged output as the primary result when available

### Limitations

- Benchmark is small (12 cases) and synthetic
- Baseline cannot handle semantic equivalence (e.g. "$75" vs "seventy-five dollars")
- LLM comparator is subject to rate limits and model changes

### Next Steps

- Larger and more diverse benchmark
- Semantic similarity layer for the baseline
- Support for additional providers (OpenAI, Gemini)
