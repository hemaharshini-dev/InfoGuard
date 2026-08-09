"""Text normalisation and fact-extraction utilities used by both comparators."""
import re


def normalize(text: str) -> str:
    """Lowercase and collapse whitespace for consistent comparisons."""
    return re.sub(r"\s+", " ", text.strip().lower())


def split_sentences(text: str) -> list[str]:
    """Split text into sentences on sentence-ending punctuation."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def extract_facts(text: str) -> set[str]:
    """Extract numbers, dates, identifiers, and capitalised proper nouns as fact tokens."""
    patterns = [
        r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b",          # numbers / amounts
        r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?\b",  # dates
        r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+\d{4})?\b",
        r"\b[A-Z]{2,}-\d+\b",                           # identifiers like ORD-6612
        r"\b\d+\s*(?:mbps|gb|tb|ghz|mhz)\b",           # technical specs
        r"\$\d+(?:\.\d{2})?",                           # dollar amounts
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",    # IP addresses
        r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b",  # emails
    ]
    text_lower = text.lower()
    facts: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text_lower, re.IGNORECASE):
            facts.add(match.group().strip().lower())
    return facts


def token_overlap(a: str, b: str) -> float:
    """Jaccard similarity between word token sets of two strings."""
    ta = set(normalize(a).split())
    tb = set(normalize(b).split())
    if not ta and not tb:
        return 1.0
    return len(ta & tb) / len(ta | tb)
