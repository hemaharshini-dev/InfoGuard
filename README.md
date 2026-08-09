# InfoGuard

An AI evaluation framework that compares transcripts against their summaries, detects mismatches, and generates structured PDF reports.

---

## What InfoGuard Does

The same information can exist in different formats. InfoGuard takes a **transcript** (the source of truth) and a **summary** (a shorter version of it) and automatically finds where they disagree.

It detects:
- **Missing information** — facts in the transcript that are absent from the summary
- **Incorrect information** — facts the summary states wrongly
- **Conflicting information** — information that clashes without resolution
- **Extra information** — things the summary adds that were never in the transcript (hallucinations)

---

## Tech Stack

| Component | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Schemas | Pydantic v2 |
| LLM Comparator | Groq API (`llama-3.3-70b-versatile`) |
| PDF Reports | ReportLab |
| Tests | pytest |
| Environment | python-dotenv + pydantic-settings |
| Runtime | Python 3.11+ |

---

## Setup

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd InfoGuard
```

### 2. Create and activate the virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -e ".[dev]"
```

### 4. Configure environment

```bash
cp .env.example .env
```

Open `.env` and add your Groq API key:

```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
LOG_LEVEL=INFO
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

---

## Running the API

```bash
.venv\Scripts\uvicorn.exe app.main:app --reload   # Windows
uvicorn app.main:app --reload                      # macOS / Linux
```

Open `http://localhost:8000/docs` for the interactive Swagger UI.

---

## API Endpoints

| Method | Endpoint | What it does |
|---|---|---|
| `GET` | `/health` | Returns API status and active model |
| `POST` | `/compare` | Runs both comparators on a transcript+summary pair, returns JSON |
| `POST` | `/benchmark` | Runs the full 12-case benchmark, returns evaluation report as JSON |
| `POST` | `/report` | Runs benchmark and returns a PDF evaluation report |
| `POST` | `/report/compare` | Runs both comparators on your input and returns a PDF comparison report |

### Example: `/compare`

```bash
curl -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Agent: The refund of $75 will be issued within 5 business days.",
    "summary": "Agent confirmed a refund within 3 business days."
  }'
```

### Example: `/report/compare`

Send the same JSON body to `/report/compare` — you will receive a PDF file download.

---

## Running the Benchmark

```bash
python -m scripts.run_evaluation
```

Runs both comparators across all 12 benchmark cases and prints a metrics summary to the terminal.

---

## Generating the PDF Report

**Benchmark report** (all 12 test cases):
```bash
python -m scripts.generate_report
```

**Single input report** (custom transcript + summary):
```bash
python -m scripts.generate_single_report
```

Both PDFs are saved to `reports/`.

---

## How the Evaluation Works

InfoGuard uses two comparison approaches:

### 1. Rule-Based Baseline
Extracts facts (numbers, dates, identifiers, dollar amounts, IPs, emails) from both texts using regex patterns, then checks for missing, extra, and conflicting values. Fast (~1ms), deterministic, no API needed.

### 2. LLM Comparator (Groq)
Sends the transcript and summary to `llama-3.3-70b-versatile` with a structured prompt. The model reasons about mismatches and returns a JSON array of issues. More accurate on nuanced and meaning-level differences (~300–800ms per case).

Both comparators return the same `ComparatorResult` schema so they can be scored and compared uniformly.

---

## Benchmark

The synthetic benchmark contains **12 cases across 6 categories**:

| Category | Cases | What it tests |
|---|---|---|
| Perfect Match | 2 | Summary fully agrees with transcript |
| Missing Fields | 2 | Summary omits key facts |
| Incorrect Values | 2 | Summary states wrong facts |
| Ambiguous | 2 | Vague transcript, hard to verify |
| Sensitive | 2 | PII handling and appropriate redaction |
| Extra | 2 | Summary hallucinates facts |

Benchmark cases are in `data/benchmark/cases.json`. Each case has a transcript, summary, and ground truth label.

---

## Evaluation Metrics

| Metric | Definition |
|---|---|
| Accuracy | Percentage of cases where the method correctly identified whether issues exist |
| Precision | Of all issues flagged, how many were actually real |
| Recall | Of all real issues, how many were caught |
| F1 Score | Combined score balancing precision and recall |
| Latency | Average time per comparison |

---

## Project Structure

```
InfoGuard/
├── app/
│   ├── api/            # FastAPI route handlers
│   ├── comparators/    # Baseline and LLM comparators
│   ├── core/           # Config and environment loading
│   ├── evaluation/     # Benchmark loader and scorer
│   ├── reporting/      # PDF builder and renderer
│   ├── schemas/        # Pydantic models
│   ├── services/       # Pipeline orchestration
│   ├── utils/          # Text normalization helpers
│   └── main.py         # FastAPI app entrypoint
├── data/
│   └── benchmark/      # Synthetic benchmark cases (cases.json)
├── docs/               # Technical report and design docs
├── reports/            # Generated PDF reports
├── scripts/            # CLI scripts for running benchmark and reports
├── tests/              # Unit and API tests
├── .env.example        # Environment variable template
├── pyproject.toml      # Dependencies and project metadata
└── README.md
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

53 tests across 5 files covering utilities, baseline comparator, benchmark loader, scorer, reporting, and API endpoints.

---

## Limitations

- Benchmark is synthetic and small (12 cases). Real-world transcripts may be more complex.
- The baseline cannot handle semantic equivalence (e.g. "$75" vs "seventy-five dollars").
- The LLM comparator is subject to Groq rate limits and model updates.
- The free Groq tier has a daily token limit — running the full benchmark repeatedly may hit it.

## Future Improvements

- Larger and more diverse benchmark
- Semantic similarity scoring for the baseline
- Response caching for LLM comparisons
- Support for additional LLM providers
