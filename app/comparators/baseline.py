"""Rule-based baseline comparator using regex fact extraction.

Fast (~1ms), deterministic, and requires no external API.
Extracts facts (numbers, dates, identifiers, dollar amounts, IPs, emails)
from both texts and diffs them to find missing, extra, and incorrect values.

Enhancement: missing and extra facts are grouped by source sentence so that
multiple tokens from the same sentence produce one issue, not one per token.
This significantly reduces false-positive noise and improves precision.
"""
import time
from app.comparators.base import BaseComparator
from app.schemas.models import (
    ComparisonInput,
    ComparatorResult,
    ComparatorName,
    Issue,
    IssueType,
)
from app.utils.text import extract_facts, normalize, split_sentences, token_overlap

# Sentence pair is "similar enough" to compare if overlap exceeds this
_SENTENCE_OVERLAP_THRESHOLD = 0.25
# A fact in the transcript is "covered" if it appears in the full summary text
_FACT_COVERAGE_THRESHOLD = 0.0  # exact substring match after normalization


class BaselineComparator(BaseComparator):
    """Deterministic comparator that diffs extracted facts between transcript and summary.

    Missing and extra facts are grouped by the sentence they originate from,
    so one sentence with three differing facts produces one issue, not three.
    """

    def compare(self, input: ComparisonInput) -> ComparatorResult:
        start = time.perf_counter()
        issues: list[Issue] = []

        transcript_facts = extract_facts(input.transcript)
        summary_facts = extract_facts(input.summary)

        # --- Missing facts: group by sentence to avoid one issue per token ---
        missing = transcript_facts - summary_facts
        if missing:
            # Find which transcript sentence each missing fact came from
            t_sentences = split_sentences(input.transcript)
            sentence_facts: dict[str, set[str]] = {}
            for fact in missing:
                source = next(
                    (s for s in t_sentences if fact in normalize(s)),
                    input.transcript[:200],
                )
                sentence_facts.setdefault(source, set()).add(fact)
            for source_sent, facts in sentence_facts.items():
                issues.append(Issue(
                    issue_type=IssueType.MISSING,
                    description=f"Facts {sorted(facts)} found in transcript but absent from summary.",
                    transcript_excerpt=source_sent[:200],
                    summary_excerpt=None,
                ))

        # --- Extra facts: group by sentence similarly ---
        extra = summary_facts - transcript_facts
        if extra:
            s_sentences = split_sentences(input.summary)
            sentence_facts_extra: dict[str, set[str]] = {}
            for fact in extra:
                source = next(
                    (s for s in s_sentences if fact in normalize(s)),
                    input.summary[:200],
                )
                sentence_facts_extra.setdefault(source, set()).add(fact)
            for source_sent, facts in sentence_facts_extra.items():
                issues.append(Issue(
                    issue_type=IssueType.EXTRA,
                    description=f"Facts {sorted(facts)} appear in summary but have no basis in transcript.",
                    transcript_excerpt=None,
                    summary_excerpt=source_sent[:200],
                ))

        # --- Incorrect / conflicting: sentence-level mismatch detection ---
        transcript_sentences = split_sentences(input.transcript)
        summary_sentences = split_sentences(input.summary)

        for s_sent in summary_sentences:
            s_norm = normalize(s_sent)
            # Find the most similar transcript sentence
            best_overlap = 0.0
            best_t_sent = ""
            for t_sent in transcript_sentences:
                ov = token_overlap(s_sent, t_sent)
                if ov > best_overlap:
                    best_overlap = ov
                    best_t_sent = t_sent

            if best_overlap < _SENTENCE_OVERLAP_THRESHOLD:
                continue  # sentences are too dissimilar to compare meaningfully

            t_norm = normalize(best_t_sent)

            # Extract facts from this sentence pair
            s_facts = extract_facts(s_sent)
            t_facts = extract_facts(best_t_sent)

            # Facts present in both sentences but with different values suggest incorrect info
            # We detect this by checking if a summary fact is numeric/specific and
            # the transcript sentence contains a different numeric/specific fact
            if s_facts and t_facts and s_facts != t_facts:
                # Only flag if the sentences are topically similar (overlap > threshold)
                conflicting_in_summary = s_facts - t_facts
                conflicting_in_transcript = t_facts - s_facts
                if conflicting_in_summary and conflicting_in_transcript:
                    issues.append(Issue(
                        issue_type=IssueType.INCORRECT,
                        description=(
                            f"Summary states {conflicting_in_summary} but transcript states "
                            f"{conflicting_in_transcript} in a similar context."
                        ),
                        transcript_excerpt=best_t_sent[:200],
                        summary_excerpt=s_sent[:200],
                    ))

        latency = time.perf_counter() - start
        return ComparatorResult(
            comparator=ComparatorName.BASELINE,
            issues=issues,
            latency_seconds=round(latency, 4),
        )
