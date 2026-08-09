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
    def compare(self, input: ComparisonInput) -> ComparatorResult:
        start = time.perf_counter()
        issues: list[Issue] = []

        transcript_norm = normalize(input.transcript)
        summary_norm = normalize(input.summary)

        transcript_facts = extract_facts(input.transcript)
        summary_facts = extract_facts(input.summary)

        # --- Missing facts: in transcript but not in summary ---
        missing = transcript_facts - summary_facts
        for fact in missing:
            issues.append(Issue(
                issue_type=IssueType.MISSING,
                description=f"Fact '{fact}' found in transcript but absent from summary.",
                transcript_excerpt=fact,
                summary_excerpt=None,
            ))

        # --- Extra facts: in summary but not in transcript ---
        extra = summary_facts - transcript_facts
        for fact in extra:
            issues.append(Issue(
                issue_type=IssueType.EXTRA,
                description=f"Fact '{fact}' appears in summary but has no basis in transcript.",
                transcript_excerpt=None,
                summary_excerpt=fact,
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

            # Extract facts from this sentence pair and check for value conflicts
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
