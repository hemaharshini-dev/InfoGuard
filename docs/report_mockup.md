# InfoGuard — Comparison Report
**Generated:** 2026-08-10 | **Type:** Single transcript vs summary analysis

---

## Overall Verdict

> **ISSUES FOUND** — The summary does not fully or accurately represent the transcript.

---

## What Was Checked

**Transcript (source of truth):**
> Agent: Can I get your name?
> Customer: Sure, I am Sarah. I was charged $150 on April 3rd but my plan is $75 per month.
> Agent: I see the error. A refund of $75 will be issued to your card ending in 9921 within 5 business days.

**Summary (checked against the transcript):**
> Customer Sarah reported a billing error. Agent confirmed a refund of $75 within 3 business days.

---

## Issues Found

### AI Analysis (Groq) — Primary

| # | Issue Type | What Was Found | In Transcript | In Summary |
|---|---|---|---|---|
| 1 | Incorrect Information | The number of business days for the refund is wrong | "within 5 business days" | "within 3 business days" |
| 2 | Missing Information | The original charge amount is not mentioned | "$150 on April 3rd" | *(not mentioned)* |
| 3 | Missing Information | The card number is not mentioned | "card ending in 9921" | *(not mentioned)* |

### Rule-Based Analysis (Baseline)

> **Note:** This method uses pattern matching on numbers, dates, and identifiers. It is faster but less nuanced — it may flag things that are technically fine.

| # | Issue Type | What Was Found |
|---|---|---|
| 1 | Missing Information | "$150" is in the transcript but not in the summary |
| 2 | Missing Information | "April 3rd" is in the transcript but not in the summary |
| 3 | Missing Information | "9921" (card number) is in the transcript but not in the summary |
| 4 | Missing Information | "5" (business days) is in the transcript but not in the summary |
| 5 | Extra Information | "3" appears in the summary but not in the transcript |
| 6 | Incorrect Information | Summary says "3" but transcript says "5" in the same context |

---

## Approach Comparison

| | Rule-Based (Baseline) | AI Analysis (Groq) |
|---|---|---|
| **How it works** | Extracts facts using pattern matching and checks if they appear in both texts | Sends the transcript and summary to an LLM and asks it to reason about mismatches |
| **Accuracy** | Good at catching exact fact differences — numbers, dates, identifiers. Misses meaning-level issues. | Better overall — understands context, paraphrasing, and subtle contradictions |
| **Speed** | ~2 ms | ~470 ms |
| **Advantages** | Free, runs locally, fully deterministic, no API needed, extremely fast | Understands language naturally, fewer false alarms, produces human-readable descriptions |
| **Limitations** | Cannot understand meaning, flags individual tokens separately, produces noise | Slower, requires internet and API key, non-deterministic, has cost |

---

## Bottom Line

The summary has **3 real problems**:
1. **Incorrect** — Refund timeline says 3 business days, transcript says 5
2. **Missing** — $150 charge amount and April 3rd date not mentioned
3. **Missing** — Card ending in 9921 not mentioned

---

## Glossary

| Term | Definition |
|---|---|
| **Missing** | A fact from the transcript is completely absent in the summary. |
| **Incorrect** | The summary states a fact that contradicts the transcript. |
| **Conflicting** | The summary contains information that clashes with the transcript without resolution. |
| **Extra / Hallucinated** | The summary adds information that was never in the transcript. |
| **Accuracy** | How often the method correctly identified whether a problem exists or not. |
| **Speed** | How long the method took to run. Lower is faster. |
| **Baseline** | The rule-based method — fast, deterministic, uses pattern matching. |
| **LLM / Groq** | The AI method — slower, uses a language model to reason about the text. |
