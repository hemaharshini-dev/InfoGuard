# InfoGuard Implementation Plan

## A. Problem Understanding

InfoGuard is a comparison and evaluation framework, not a generic chatbot. The assignment is to compare two versions of the same underlying information, detect mismatches, and produce a structured evaluation report. For this submission, the chosen use case is Transcript vs Summary, with an API-first FastAPI application, a Groq-backed LLM comparison approach, a non-LLM baseline approach, a synthetic benchmark, and PDF report output.

The core engineering goal is to build something that is easy to review, easy to run, and easy to trust: strong schemas, clear evaluation logic, reproducible test cases, and a professional repository structure. The assignment explicitly asks for comparison of at least two approaches, coverage of specific test-case categories, and structured reporting. Everything in the plan below is constrained to those requirements.

## B. Requirements Extracted from problem_statement.md

### Explicit requirements

- Build an AI evaluation framework that compares two versions of the same information.
- Detect missing information.
- Detect incorrect information.
- Detect conflicting information.
- Detect extra information, including hallucinations.
- Generate a structured evaluation report.
- Choose one use case.
- Study at least two approaches for comparing documents.
- Compare accuracy, speed, advantages, and limitations.
- Create test cases containing perfect matches, missing fields, incorrect values, ambiguous cases, and sensitive information.

### Suggested technologies in the brief

- Python.
- OpenAI, Gemini, or Claude API.
- FastAPI.

### Engineering recommendations

- Use a clean service architecture with separate comparator, evaluation, and reporting layers.
- Produce both machine-readable and human-readable outputs internally, even if the final deliverable is PDF.
- Keep the benchmark synthetic and small but balanced.
- Make the LLM provider swappable so the framework is not locked to one vendor.
- Add a local cache and consistent typed schemas to improve repeatability and maintainability.

## C. Proposed Use Case

Chosen use case: Transcript vs Summary.

Why this is the best fit:

- It directly matches the assignment’s “same information, different formats” framing.
- It naturally produces missing, incorrect, conflicting, and extra-content cases.
- It is easy to create synthetic benchmark items with labeled ground truth.
- It avoids extra pipeline complexity like OCR or speech recognition.
- It is easy to explain in the report and demo.

What the system will compare:

- A transcript containing the source conversation.
- A summary containing a shorter representation of that conversation.
- The system will verify whether the summary preserves the transcript’s factual content.

## D. Architecture

### High-level system flow

- Input transcript and summary pair.
- Normalize both texts into comparable structures.
- Run two comparison approaches.
- Convert each approach’s output into a common issue schema.
- Score predictions against benchmark ground truth.
- Aggregate results across the dataset.
- Generate a structured report and render it to PDF.

### Recommended architectural layers

- API layer: receives requests and exposes evaluation endpoints.
- Core layer: configuration, environment loading, provider abstraction, shared constants.
- Normalization layer: prepares transcript and summary text for comparison.
- Comparator layer: implements baseline and LLM-based comparison methods.
- Evaluation layer: computes metrics and aggregates benchmark results.
- Reporting layer: creates JSON/Markdown intermediate output and final PDF.
- Test data layer: stores benchmark cases and labels.
- Test layer: validates each component and end-to-end behavior.

### Data flow from input to final report

- A transcript-summary pair is submitted.
- The normalizer cleans and segments the text into factual units.
- The baseline comparator checks coverage using deterministic heuristics.
- The LLM comparator uses Groq to produce structured mismatch detection.
- The evaluator compares both predictions to labeled benchmark truth.
- Metrics are computed per test case and aggregated overall.
- The reporter writes a structured evaluation summary and renders a PDF.

Design principle:

- All comparison methods should return the same schema so they can be scored uniformly. This keeps the framework maintainable and makes future comparators easy to add.

## E. Project Folder Structure

- app/
- app/api/
- app/core/
- app/services/
- app/comparators/
- app/evaluation/
- app/reporting/
- app/schemas/
- app/utils/
- data/
- data/benchmark/
- data/raw/
- data/processed/
- reports/
- docs/
- tests/
- scripts/
- README.md
- pyproject.toml
- .env.example

This structure is professional without being overbuilt. It cleanly separates orchestration, comparison logic, evaluation, and reporting.

## F. File-by-File Responsibilities

### app/main.py

Application entrypoint. Creates the FastAPI app, registers routes, and wires dependencies.

### app/api/

Contains route handlers for evaluation submission, benchmark execution, report generation, and health checks. This layer should be thin.

### app/core/

Holds configuration objects, environment loading, API provider settings, and shared constants. This is where the Groq API configuration should live.

### app/services/

Orchestrates the end-to-end pipeline. It should coordinate normalization, comparator execution, scoring, and reporting.

### app/comparators/

Contains the two required comparison approaches. Each comparator should implement the same interface and output the same issue schema.

### app/evaluation/

Contains benchmark loading, label handling, scoring logic, metric computation, and aggregation.

### app/reporting/

Generates structured output, including PDF rendering. It should transform evaluation results into a polished report artifact.

### app/schemas/

Defines Pydantic models for input pairs, issue detection, comparator outputs, benchmark items, metrics, and report payloads.

### app/utils/

Reusable helpers for text cleanup, timing, formatting, and small pure functions.

### data/benchmark/

Synthetic benchmark cases and labels covering all required categories.

### data/raw/

Optional source material or draft transcript-summary examples if you want to store generation inputs separately.

### data/processed/

Normalized or derived benchmark artifacts.

### reports/

Final generated PDF reports and any supporting artifacts.

### docs/

Technical report, demo notes, and design documentation.

### tests/

Unit, integration, and report-validation tests.

### scripts/

Utility scripts for running the benchmark, generating the report, or producing demo outputs.

### README.md

Project overview, setup steps, usage, benchmark description, evaluation summary, and links to outputs.

### pyproject.toml

Dependencies, packaging metadata, and tool configuration.

### .env.example

Example environment variables for Groq API keys and runtime options.

## G. Technology Choices

### Recommended stack

- Python 3.11 or newer.
- FastAPI for API-first delivery.
- Pydantic for strict schemas.
- Groq API for the LLM-based comparator.
- pytest for tests.
- Uvicorn for local API serving.
- ReportLab or WeasyPrint for PDF generation.
- python-dotenv or equivalent for environment loading.

### Why each is needed

- Python is the core implementation language and is explicitly suggested.
- FastAPI gives a clean, reviewer-friendly API surface.
- Pydantic keeps inputs and outputs typed and stable.
- Groq is the chosen LLM provider for the comparison approach.
- pytest supports regression testing and benchmark validation.
- Uvicorn serves the API locally.
- ReportLab or WeasyPrint converts the structured report into PDF.
- Environment loading keeps the API key handling clean.

Engineering recommendation:

- Keep the LLM provider behind a small adapter interface so the system can switch providers later without touching the evaluator or report generator.

## H. Comparison Approaches

The assignment requires at least two approaches. Recommended approaches:

### 1. Deterministic baseline comparator

Rule-based alignment and coverage checks over normalized content. It provides a stable reference point and is easy to explain.

### 2. Groq-based LLM comparator

Prompt the model to compare transcript and summary content and return structured issue detections in the same schema as the baseline.

Why this pair works well:

- The baseline is fast, cheap, and deterministic.
- The Groq comparator is more flexible and can handle nuanced mismatches better.
- The contrast makes evaluation meaningful because the two approaches differ in both performance characteristics and behavior.

How they should be evaluated:

- Accuracy on labeled benchmark cases.
- Speed per case and average throughput.
- Strengths on ambiguous cases.
- Limitations on sensitive or subtle mismatches.
- Consistency of structured outputs.

Recommendation:

- Do not add more approaches for MVP. Two well-executed methods are enough and align exactly with the brief.

## I. Dataset and Evaluation Plan

### Required benchmark categories from the brief

- Perfect matches.
- Missing fields.
- Incorrect values.
- Ambiguous cases.
- Sensitive information.

### Recommended benchmark design

- Create a small but balanced synthetic set.
- Ensure each category appears multiple times.
- Include some cases with more than one issue type.
- Keep labels explicit and human-auditable.
- Store ground truth in a structured schema.

### Example benchmark composition

- Perfect matches: transcript and summary fully agree.
- Missing fields: summary omits a factual item from the transcript.
- Incorrect values: summary states a wrong fact.
- Ambiguous cases: summary is partially supported but not fully clear.
- Sensitive information: transcript contains sensitive facts that the summary should preserve or redact depending on the test intent.

### Evaluation workflow

- Run both comparators on every test item.
- Compare outputs against labeled truth.
- Record per-case predictions and errors.
- Aggregate category-level and overall results.
- Identify typical failure patterns by approach.

Important recommendation:

- Keep the benchmark synthetic unless you have a strong reason to use real examples. Synthetic cases make the assignment cleaner, safer, and easier to defend in a hiring review.

## J. Metrics

### Explicitly required by the brief

- Accuracy.
- Speed.
- Advantages.
- Limitations.

### Recommended computed metrics

- Case-level correctness.
- Issue-type precision.
- Issue-type recall.
- Issue-type F1 score.
- Average latency per comparison.
- Category-level accuracy by benchmark type.

### How to present metrics

- Include a comparison table for the two approaches.
- Show overall averages.
- Show performance by test-case category.
- Add a short narrative explaining where each approach works best.

Recommendation:

- Keep the metrics readable and practical. Do not overcomplicate the scoring model unless the assignment asks for it.

## K. Testing Strategy

### Unit tests

- Normalization logic.
- Comparator output formatting.
- Metric computation.
- PDF report assembly helpers.

### Integration tests

- End-to-end comparison on a benchmark item.
- End-to-end benchmark run across multiple cases.
- PDF generation from evaluation results.

### API tests

- Health endpoint.
- Evaluation endpoint.
- Report-generation endpoint.

### Quality checks

- Validate that every benchmark category is represented.
- Validate that both approaches emit the same result schema.
- Validate that reports include all required summary sections.

Recommendation:

- Include at least one golden-file style test for the report structure so the final PDF pipeline stays stable.

## L. Technical Report Structure

The required 2–3 page technical report should be concise and structured.

### Suggested outline

- Problem statement and goal.
- Chosen use case.
- System architecture.
- Comparison approaches.
- Benchmark design.
- Metrics and results.
- Strengths, limitations, and next steps.

### Recommended content strategy

- One table comparing the two approaches.
- One small example case.
- One short paragraph on evaluation methodology.
- One short conclusion about which approach is more appropriate and why.

## M. README Structure

### Recommended README sections

- What InfoGuard is.
- Chosen use case.
- What problems it solves.
- Tech stack.
- Setup instructions.
- How to configure Groq.
- How to run the API.
- How to run the benchmark.
- How to generate the PDF report.
- How the evaluation works.
- Project structure.
- Testing instructions.
- Limitations and future improvements.

Recommendation:

- Make the README suitable for a recruiter or reviewer who wants to run the project quickly without reading the code first.

## N. 5-Minute Demo Plan

### Suggested flow

- Introduce the transcript vs summary use case.
- Show one perfect match example.
- Show one mismatch example.
- Run both comparison approaches.
- Display the structured comparison output.
- Show the generated PDF report.
- Summarize the accuracy and speed tradeoff.
- Mention known limitations and why the final design is clean.

Recommendation:

- Keep the demo focused on evaluation and reporting, not on UI polish or unrelated features.

## O. MVP vs Optional Enhancements

### MVP required to satisfy the assignment

- Transcript vs summary use case.
- FastAPI API-first interface.
- Groq-based LLM comparator.
- Deterministic baseline comparator.
- Synthetic benchmark with required categories.
- Structured evaluation metrics.
- PDF report output.
- Tests.
- README.
- Technical report.

### Optional enhancements

- Additional comparator approach.
- HTML version of the report.
- Cached benchmark runs.
- More benchmark cases.
- More detailed visualizations.
- Optional manual review endpoint.
- Export of intermediate JSON results.

Recommendation:

- Finish the MVP completely before adding enhancements. A polished core submission is better than a broad but shallow one.

## P. Step-by-Step Implementation Order

### Phase 1: Scope and contracts

- Lock the use case and output expectations.
- Define schemas for inputs, issues, metrics, and reports.
- Define the common comparison result format.

### Phase 2: Benchmark design

- Create the synthetic benchmark cases.
- Label each case with ground truth.
- Ensure all required categories are represented.

### Phase 3: Baseline comparator

- Implement the deterministic comparator.
- Normalize transcript and summary content.
- Produce structured issue outputs.

### Phase 4: Groq comparator

- Add Groq API integration.
- Implement the prompt and output parser.
- Match the baseline output schema.

### Phase 5: Evaluation engine

- Score predictions against labels.
- Compute metrics.
- Aggregate results by category and overall.

### Phase 6: Reporting

- Build the structured report model.
- Render the report to PDF.
- Save final artifacts in a predictable location.

### Phase 7: API layer

- Add FastAPI endpoints for running comparisons and benchmarks.
- Expose report-generation endpoints.
- Add health and metadata endpoints.

### Phase 8: Testing and hardening

- Add unit, integration, and API tests.
- Validate benchmark coverage.
- Check PDF report output.

### Phase 9: Documentation

- Write the README.
- Write the technical report.
- Prepare demo notes and screenshots if needed.

### Phase 10: Final review

- Run the full benchmark.
- Verify metrics and PDF output.
- Ensure the repository reads cleanly for a hiring reviewer.

## Q. Open Questions Before Implementation

No more input is required to proceed with the plan, because the major choices are already resolved:

- Transcript vs summary is confirmed.
- Groq is confirmed.
- FastAPI API-first is confirmed.
- Synthetic benchmark is the right default.
- PDF is the required report format.

Optional decision, if you want to be specific later:

- Whether the final PDF should be generated directly from Markdown or from a structured intermediate report model.

Recommendation:

- Use a structured report model first, then render to PDF, because it is more maintainable and less brittle.
