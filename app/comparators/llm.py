"""LLM comparator using Groq's llama-3.3-70b-versatile model.

Sends the transcript and summary to the Groq API with a structured prompt
and parses the JSON array response into Issue objects.
More accurate than the baseline on nuanced, meaning-level differences.

Responses are cached to disk (data/cache/) keyed by a SHA-256 hash of the
(model, transcript, summary) tuple. Identical inputs never hit the API twice.
"""
import hashlib
import json
import time
from pathlib import Path
from groq import Groq
from app.comparators.base import BaseComparator
from app.core.config import settings
from app.schemas.models import (
    ComparisonInput,
    ComparatorResult,
    ComparatorName,
    Issue,
    IssueType,
)

_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(model: str, transcript: str, summary: str) -> str:
    """SHA-256 hash of model + inputs — used as the cache filename."""
    payload = f"{model}||{transcript}||{summary}"
    return hashlib.sha256(payload.encode()).hexdigest()

_SYSTEM_PROMPT = """You are an expert fact-checker comparing a transcript against its summary.

Your job is to identify every mismatch between the transcript (ground truth) and the summary.

Respond ONLY with a valid JSON array. Each element must have exactly these fields:
- "issue_type": one of "missing", "incorrect", "conflicting", "extra"
- "description": a concise explanation of the issue
- "transcript_excerpt": the relevant excerpt from the transcript (or null)
- "summary_excerpt": the relevant excerpt from the summary (or null)
- "confidence": a float between 0.0 and 1.0 indicating how confident you are this is a real issue

If there are no issues, respond with an empty array: []

Do not include any text outside the JSON array."""

_USER_TEMPLATE = """TRANSCRIPT:
{transcript}

SUMMARY:
{summary}

Identify all factual mismatches between the transcript and the summary."""


class LLMComparator(BaseComparator):
    """Calls the Groq API to detect mismatches using a large language model."""

    def __init__(self) -> None:
        self._client = Groq(api_key=settings.groq_api_key)

    def compare(self, input: ComparisonInput) -> ComparatorResult:
        """Return cached result if available, otherwise call the Groq API and cache the response."""
        key = _cache_key(settings.groq_model, input.transcript, input.summary)
        cache_file = _CACHE_DIR / f"{key}.json"

        # --- Cache hit: deserialise and return immediately, no API call ---
        if cache_file.exists():
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            return ComparatorResult.model_validate(cached)

        start = time.perf_counter()

        user_message = _USER_TEMPLATE.format(
            transcript=input.transcript,
            summary=input.summary,
        )

        response = self._client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
        )

        latency = time.perf_counter() - start
        raw = response.choices[0].message.content.strip()

        issues = self._parse(raw)

        result = ComparatorResult(
            comparator=ComparatorName.LLM,
            issues=issues,
            latency_seconds=round(latency, 4),
            raw_output=raw,
        )
        # --- Cache miss: persist result so future runs skip the API call ---
        cache_file.write_text(result.model_dump_json(), encoding="utf-8")
        return result

    def _parse(self, raw: str) -> list[Issue]:
        """Parse the LLM's JSON response into Issue objects, stripping markdown fences if present."""
        try:
            # Strip markdown code fences if model wraps output
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text.strip())
        except json.JSONDecodeError:
            return [Issue(
                issue_type=IssueType.EXTRA,
                description=f"LLM returned non-JSON output: {raw[:200]}",
            )]

        issues: list[Issue] = []
        for item in data:
            try:
                raw_conf = item.get("confidence")
                confidence = float(raw_conf) if raw_conf is not None else None
                issues.append(Issue(
                    issue_type=IssueType(item["issue_type"]),
                    description=item.get("description", ""),
                    transcript_excerpt=item.get("transcript_excerpt"),
                    summary_excerpt=item.get("summary_excerpt"),
                    confidence=confidence,
                ))
            except (KeyError, ValueError):
                continue
        return issues
