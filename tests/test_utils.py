from app.utils.text import normalize, split_sentences, extract_facts, token_overlap


def test_normalize_lowercases_and_strips():
    assert normalize("  Hello World  ") == "hello world"


def test_normalize_collapses_whitespace():
    assert normalize("hello   world") == "hello world"


def test_split_sentences_basic():
    text = "Hello world. How are you? I am fine."
    parts = split_sentences(text)
    assert len(parts) == 3


def test_extract_facts_dollar_amount():
    facts = extract_facts("The refund is $75.")
    assert "$75" in facts


def test_extract_facts_identifier():
    facts = extract_facts("Order ORD-6612 was updated.")
    assert "ord-6612" in facts


def test_extract_facts_date():
    facts = extract_facts("The call was on March 5th.")
    assert "march 5th" in facts


def test_extract_facts_ip():
    facts = extract_facts("Login from 192.168.10.45 detected.")
    assert "192.168.10.45" in facts


def test_extract_facts_email():
    facts = extract_facts("Contact user@example.com for help.")
    assert "user@example.com" in facts


def test_token_overlap_identical():
    assert token_overlap("hello world", "hello world") == 1.0


def test_token_overlap_no_overlap():
    assert token_overlap("hello world", "foo bar") == 0.0


def test_token_overlap_partial():
    score = token_overlap("hello world", "hello there")
    assert 0.0 < score < 1.0
