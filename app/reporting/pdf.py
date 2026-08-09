from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
_BRAND      = colors.HexColor("#1a1a2e")
_ACCENT     = colors.HexColor("#4f8ef7")
_LIGHT      = colors.HexColor("#eef3ff")
_GREEN      = colors.HexColor("#1e8449")
_GREEN_BG   = colors.HexColor("#eafaf1")
_RED        = colors.HexColor("#c0392b")
_RED_BG     = colors.HexColor("#fdedec")
_ORANGE     = colors.HexColor("#d35400")
_ORANGE_BG  = colors.HexColor("#fef5e7")
_GRAY       = colors.HexColor("#7f8c8d")
_LGRAY      = colors.HexColor("#f4f6f7")
_DIVIDER    = colors.HexColor("#d0d0d0")

_ISSUE_META = {
    "missing":     (_RED,    _RED_BG,    "Missing Information"),
    "incorrect":   (_RED,    _RED_BG,    "Incorrect Information"),
    "conflicting": (_ORANGE, _ORANGE_BG, "Conflicting Information"),
    "extra":       (_ORANGE, _ORANGE_BG, "Extra / Hallucinated Information"),
}

_ISSUE_DEFINITIONS = {
    "Missing":              "A fact from the transcript is completely absent in the summary.",
    "Incorrect":            "The summary states a fact that contradicts the transcript.",
    "Conflicting":          "The summary contains information that clashes with the transcript without resolution.",
    "Extra / Hallucinated": "The summary adds information that was never in the transcript.",
}

_GLOSSARY_SINGLE = {
    "Missing":              "A fact from the transcript is completely absent in the summary.",
    "Incorrect":            "The summary states a fact that contradicts the transcript.",
    "Conflicting":          "The summary contains information that clashes with the transcript without resolution.",
    "Extra / Hallucinated": "The summary adds information that was never in the transcript.",
    "Accuracy":             "How often the method correctly identified whether a problem exists or not.",
    "Speed":                "How long the method took to run. Lower is faster.",
    "Baseline":             "The rule-based method — fast, deterministic, uses pattern matching.",
    "LLM / Groq":           "The AI method — slower, uses a language model to reason about the text.",
}

_GLOSSARY_BENCHMARK = {
    "Missing":              "A fact from the transcript is completely absent in the summary.",
    "Incorrect":            "The summary states a fact that contradicts the transcript.",
    "Conflicting":          "The summary contains information that clashes with the transcript without resolution.",
    "Extra / Hallucinated": "The summary adds information that was never in the transcript.",
    "Accuracy":             "Out of all cases checked, the percentage the method got completely right.",
    "Precision":            "Of all the issues flagged, how many were actually real problems.",
    "Recall":               "Of all the real problems that exist, how many were actually caught.",
    "F1 Score":             "A single score combining Precision and Recall — 1.0 is perfect, 0.0 is completely wrong.",
    "Latency":              "How long the method took to run per case. Lower is faster.",
    "Baseline":             "The rule-based method — fast, deterministic, uses pattern matching.",
    "LLM / Groq":           "The AI method — slower, uses a language model to reason about the text.",
}

# ---------------------------------------------------------------------------
# Page geometry — A4 with 2cm margins = 17.5cm usable width
# ---------------------------------------------------------------------------
_PAGE_W = 17.5 * cm


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("AppTitle",   parent=s["Title"],    textColor=_BRAND, fontSize=22, spaceAfter=4))
    s.add(ParagraphStyle("SubTitle",   parent=s["Normal"],   textColor=_GRAY,  fontSize=10, spaceAfter=8))
    s.add(ParagraphStyle("H2",         parent=s["Heading2"], textColor=_BRAND, fontSize=12, spaceBefore=14, spaceAfter=5))
    s.add(ParagraphStyle("Body",       parent=s["Normal"],   fontSize=9,  leading=14))
    s.add(ParagraphStyle("BodyBold",   parent=s["Normal"],   fontSize=9,  leading=14, fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("Small",      parent=s["Normal"],   fontSize=8,  leading=12, textColor=_GRAY))
    s.add(ParagraphStyle("VerdictOK",  parent=s["Normal"],   fontSize=12, textColor=_GREEN,  fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("VerdictBAD", parent=s["Normal"],   fontSize=12, textColor=_RED,    fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("Cell",       parent=s["Normal"],   fontSize=8,  leading=12))
    s.add(ParagraphStyle("CellGray",   parent=s["Normal"],   fontSize=8,  leading=12, textColor=_GRAY))
    s.add(ParagraphStyle("Excerpt",    parent=s["Normal"],   fontSize=8,  leading=12, textColor=_GRAY, leftIndent=6))
    return s


# ---------------------------------------------------------------------------
# Shared table style
# ---------------------------------------------------------------------------
def _tbl(header_bg=_BRAND, col_aligns=None):
    base = [
        ("BACKGROUND",    (0, 0), (-1, 0),  header_bg),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, _LIGHT]),
        ("GRID",          (0, 0), (-1, -1), 0.4, _DIVIDER),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]
    if col_aligns:
        for col, align in col_aligns:
            base.append(("ALIGN", (col, 0), (col, -1), align))
    return TableStyle(base)


def _p(text, style):
    """Wrap text in Paragraph for safe cell rendering."""
    return Paragraph(str(text), style)


# ---------------------------------------------------------------------------
# Issue card — coloured box per issue
# ---------------------------------------------------------------------------
def _issue_card(issue: dict, s) -> list:
    itype = issue.get("type", "missing")
    text_color, bg_color, label = _ISSUE_META.get(itype, (_GRAY, _LGRAY, itype.title()))
    desc = issue.get("description", "")
    t_exc = issue.get("transcript_excerpt")
    s_exc = issue.get("summary_excerpt")

    label_style = ParagraphStyle("IL", parent=s["Cell"], textColor=text_color,
                                 fontName="Helvetica-Bold", fontSize=8)
    tbl = Table(
        [[_p(label, label_style), _p(desc, s["Cell"])]],
        colWidths=[4.2 * cm, 13.3 * cm],
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg_color),
        ("BOX",           (0, 0), (-1, -1), 0.8, text_color),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    elems = [tbl]
    if t_exc:
        elems.append(_p(f'In transcript: "{t_exc}"', s["Excerpt"]))
    if s_exc:
        elems.append(_p(f'In summary: "{s_exc}"', s["Excerpt"]))
    elems.append(Spacer(1, 0.18 * cm))
    return elems


# ---------------------------------------------------------------------------
# Glossary section — shared by both report types
# ---------------------------------------------------------------------------
def _glossary(glossary: dict, s) -> list:
    elems = [
        Paragraph("Glossary", s["H2"]),
        Paragraph("One-line definition of every term used in this report.", s["Body"]),
        Spacer(1, 0.15 * cm),
    ]
    rows = [["Term", "Definition"]]
    for term, defn in glossary.items():
        rows.append([_p(f"<b>{term}</b>", s["Cell"]), _p(defn, s["Cell"])])
    t = Table(rows, colWidths=[4 * cm, 13.5 * cm])
    t.setStyle(_tbl(header_bg=_BRAND))
    elems += [t, Spacer(1, 0.3 * cm)]
    return elems


# ---------------------------------------------------------------------------
# SINGLE REPORT
# ---------------------------------------------------------------------------
def _render_single(data: dict, story: list, s):
    has_issues = bool(data["issue_types_found"])

    # 1. Overall Verdict
    story.append(Paragraph("Overall Verdict", s["H2"]))
    vstyle = s["VerdictBAD"] if has_issues else s["VerdictOK"]
    story.append(Paragraph(data["verdict"], vstyle))
    story.append(Spacer(1, 0.25 * cm))

    # 2. What Was Checked
    story.append(Paragraph("What Was Checked", s["H2"]))
    story.append(Paragraph("Transcript (source of truth):", s["BodyBold"]))
    transcript_text = data["transcript"].replace("\n", "<br/>")
    story.append(Paragraph(transcript_text, s["Body"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Summary (checked against the transcript):", s["BodyBold"]))
    story.append(Paragraph(data["summary"], s["Body"]))
    story.append(Spacer(1, 0.25 * cm))

    # 3. Issues Found — AI primary
    story.append(Paragraph("Issues Found", s["H2"]))
    story.append(Paragraph(
        "<b>AI Analysis (Groq)</b> — primary result. "
        "The AI reads both texts and reasons about what is missing, wrong, or fabricated.",
        s["Body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    if data["llm_issues"]:
        for issue in data["llm_issues"]:
            story += _issue_card(issue, s)
    else:
        story.append(Paragraph(
            "No issues found. The summary accurately reflects the transcript.", s["Body"]
        ))
    story.append(Spacer(1, 0.15 * cm))

    story.append(Paragraph(
        "<b>Rule-Based Analysis (Baseline)</b> — uses pattern matching on numbers, dates, and identifiers. "
        "Faster but less nuanced — may flag things that are technically fine.",
        s["Body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    if data["baseline_issues"]:
        for issue in data["baseline_issues"]:
            story += _issue_card(issue, s)
    else:
        story.append(Paragraph("No issues detected.", s["Body"]))
    story.append(Spacer(1, 0.25 * cm))

    # 4. Approach Comparison (accuracy, speed, advantages, limitations)
    story.append(Paragraph("Approach Comparison", s["H2"]))
    story.append(Paragraph(
        "The two methods differ in how they work, how fast they are, and what they are good at.",
        s["Body"]
    ))
    story.append(Spacer(1, 0.15 * cm))

    comp_rows = [
        ["", _p("<b>Rule-Based (Baseline)</b>", s["Cell"]), _p("<b>AI Analysis (Groq)</b>", s["Cell"])],
        [_p("<b>How it works</b>", s["Cell"]),
         _p("Extracts facts using pattern matching and checks if they appear in both texts.", s["Cell"]),
         _p("Sends the transcript and summary to an LLM and asks it to reason about mismatches.", s["Cell"])],
        [_p("<b>Accuracy</b>", s["Cell"]),
         _p("Good at catching exact fact differences — numbers, dates, identifiers. Misses meaning-level issues.", s["Cell"]),
         _p("Better overall — understands context, paraphrasing, and subtle contradictions.", s["Cell"])],
        [_p("<b>Speed</b>", s["Cell"]),
         _p(f"{data['baseline_latency']*1000:.1f} ms", s["Cell"]),
         _p(f"{data['llm_latency']*1000:.0f} ms", s["Cell"])],
        [_p("<b>Advantages</b>", s["Cell"]),
         _p("Free, runs locally, fully deterministic, no API needed, extremely fast.", s["Cell"]),
         _p("Understands language naturally, fewer false alarms, produces human-readable descriptions.", s["Cell"])],
        [_p("<b>Limitations</b>", s["Cell"]),
         _p("Cannot understand meaning, flags individual tokens separately, produces noise.", s["Cell"]),
         _p("Slower, requires internet and API key, non-deterministic, has cost.", s["Cell"])],
    ]
    tc = Table(comp_rows, colWidths=[3.2 * cm, 7.15 * cm, 7.15 * cm])
    tc.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  _BRAND),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("BACKGROUND",    (0, 1), (0, -1),  _LIGHT),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.4, _DIVIDER),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, _LIGHT]),
    ]))
    story += [tc, Spacer(1, 0.25 * cm)]

    # 5. Bottom Line
    story.append(Paragraph("Bottom Line", s["H2"]))
    llm_count = len(data["llm_issues"])
    if llm_count == 0:
        story.append(Paragraph(
            "Both methods agree: the summary is accurate. No issues were found.", s["Body"]
        ))
    else:
        story.append(Paragraph(
            f"The AI found <b>{llm_count} issue(s)</b> in the summary:", s["Body"]
        ))
        story.append(Spacer(1, 0.1 * cm))
        for i, issue in enumerate(data["llm_issues"], 1):
            _, _, label = _ISSUE_META.get(issue["type"], (_GRAY, _LGRAY, issue["type"].title()))
            story.append(_p(f"{i}. <b>{label}</b> — {issue['description']}", s["Body"]))
    story.append(Spacer(1, 0.25 * cm))

    # 6. Glossary
    story += _glossary(_GLOSSARY_SINGLE, s)


# ---------------------------------------------------------------------------
# BENCHMARK REPORT
# ---------------------------------------------------------------------------
def _render_benchmark(data: dict, story: list, s):

    # What is this report
    story.append(Paragraph("What Is This Report?", s["H2"]))
    story.append(Paragraph(
        f"InfoGuard was tested on <b>{data['total_cases']} carefully designed transcript-summary pairs</b>, "
        "each representing a different type of real-world problem. "
        "Two methods were used to detect issues: a fast rule-based method (Baseline) and an AI-powered "
        "method (Groq). This report shows how well each method performed.",
        s["Body"]
    ))
    story.append(Spacer(1, 0.25 * cm))

    # 1. Overall Results
    story.append(Paragraph("1. Overall Results", s["H2"]))
    story.append(Paragraph(
        "Accuracy = out of all test cases, in how many did the method correctly identify "
        "whether there was a problem or not.",
        s["Body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    overview = [
        ["Method", "Accuracy", "Avg. Time Per Case"],
        [_p("Rule-Based (Baseline)", s["Cell"]),
         _p(f"{data['baseline']['overall_accuracy']:.0%}", s["Cell"]),
         _p(f"{data['baseline']['avg_latency']*1000:.1f} ms", s["Cell"])],
        [_p("AI Analysis (Groq)", s["Cell"]),
         _p(f"{data['llm']['overall_accuracy']:.0%}", s["Cell"]),
         _p(f"{data['llm']['avg_latency']*1000:.0f} ms", s["Cell"])],
    ]
    t = Table(overview, colWidths=[7 * cm, 5 * cm, 5.5 * cm])
    t.setStyle(_tbl(col_aligns=[(1, "CENTER"), (2, "CENTER")]))
    story += [t, Spacer(1, 0.25 * cm)]

    # 2. Accuracy by Category
    story.append(Paragraph("2. Accuracy by Problem Type", s["H2"]))
    story.append(Paragraph(
        "The test cases were grouped into 6 categories. "
        "Here is how accurately each method handled each one.",
        s["Body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    cat_desc = {
        "perfect_match":    "Summary is fully correct — no issues should be flagged",
        "missing_fields":   "Summary leaves out important facts from the transcript",
        "incorrect_values": "Summary states something that contradicts the transcript",
        "ambiguous":        "Transcript is vague — hard to verify the summary",
        "sensitive":        "Transcript contains personal or sensitive information",
        "extra":            "Summary adds information that was never in the transcript",
    }
    cat_rows = [["Problem Type", "What It Tests", "Baseline", "AI (Groq)"]]
    for cat in sorted(data["baseline"]["category_accuracy"].keys()):
        cat_rows.append([
            _p(cat.replace("_", " ").title(), s["Cell"]),
            _p(cat_desc.get(cat, ""), s["Cell"]),
            _p(f"{data['baseline']['category_accuracy'].get(cat, 0):.0%}", s["Cell"]),
            _p(f"{data['llm']['category_accuracy'].get(cat, 0):.0%}", s["Cell"]),
        ])
    t2 = Table(cat_rows, colWidths=[3.5 * cm, 8.5 * cm, 2.5 * cm, 3 * cm])
    t2.setStyle(_tbl(col_aligns=[(2, "CENTER"), (3, "CENTER")]))
    story += [t2, Spacer(1, 0.25 * cm)]

    # 3. Detailed metrics — issue type descriptions then numbers
    story.append(Paragraph("3. Detailed Performance by Issue Type", s["H2"]))
    story.append(Paragraph(
        "For each type of issue: "
        "<b>Precision</b> = when it flags something, is it right? "
        "<b>Recall</b> = does it catch all real issues? "
        "<b>F1</b> = overall balance of both. All scores 0–1, closer to 1 is better.",
        s["Body"]
    ))
    story.append(Spacer(1, 0.15 * cm))

    # Issue type definitions table
    def_rows = [["Issue Type", "What It Means"]]
    for itype, defn in _ISSUE_DEFINITIONS.items():
        def_rows.append([_p(itype, s["Cell"]), _p(defn, s["Cell"])])
    td = Table(def_rows, colWidths=[4 * cm, 13.5 * cm])
    td.setStyle(_tbl(header_bg=_ACCENT))
    story += [td, Spacer(1, 0.15 * cm)]

    # Numeric metrics table
    num_rows = [["Issue Type", "Baseline Precision", "Baseline Recall", "Baseline F1",
                 "AI Precision", "AI Recall", "AI F1"]]
    for row in data["comparison_table"]:
        num_rows.append([
            _p(row["issue_type"].title(), s["Cell"]),
            _p(f"{row['baseline_precision']:.2f}", s["Cell"]),
            _p(f"{row['baseline_recall']:.2f}", s["Cell"]),
            _p(f"{row['baseline_f1']:.2f}", s["Cell"]),
            _p(f"{row['llm_precision']:.2f}", s["Cell"]),
            _p(f"{row['llm_recall']:.2f}", s["Cell"]),
            _p(f"{row['llm_f1']:.2f}", s["Cell"]),
        ])
    col_w = [3.5 * cm, 2.3 * cm, 2.3 * cm, 2.1 * cm, 2.3 * cm, 2.3 * cm, 2.2 * cm]
    t3 = Table(num_rows, colWidths=col_w)
    t3.setStyle(_tbl(col_aligns=[(i, "CENTER") for i in range(1, 7)]))
    story += [t3, Spacer(1, 0.25 * cm)]

    # 4. Approach Comparison
    story.append(Paragraph("4. Approach Comparison", s["H2"]))
    story.append(Paragraph(
        "How the two methods compare on accuracy, speed, advantages, and limitations.",
        s["Body"]
    ))
    story.append(Spacer(1, 0.15 * cm))
    comp_rows = [
        ["", _p("<b>Rule-Based (Baseline)</b>", s["Cell"]), _p("<b>AI Analysis (Groq)</b>", s["Cell"])],
        [_p("<b>Accuracy</b>", s["Cell"]),
         _p("Good at catching exact fact differences — numbers, dates, identifiers. Misses meaning-level issues.", s["Cell"]),
         _p("Better overall — understands context, paraphrasing, and subtle contradictions.", s["Cell"])],
        [_p("<b>Speed</b>", s["Cell"]),
         _p(f"~{data['baseline']['avg_latency']*1000:.1f} ms per case", s["Cell"]),
         _p(f"~{data['llm']['avg_latency']*1000:.0f} ms per case", s["Cell"])],
        [_p("<b>Advantages</b>", s["Cell"]),
         _p("Free, runs locally, fully deterministic, no API needed, extremely fast.", s["Cell"]),
         _p("Understands language naturally, fewer false alarms, produces human-readable descriptions.", s["Cell"])],
        [_p("<b>Limitations</b>", s["Cell"]),
         _p("Cannot understand meaning, flags individual tokens separately, produces noise.", s["Cell"]),
         _p("Slower, requires internet and API key, non-deterministic, has cost.", s["Cell"])],
    ]
    tc = Table(comp_rows, colWidths=[3.2 * cm, 7.15 * cm, 7.15 * cm])
    tc.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  _BRAND),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("BACKGROUND",    (0, 1), (0, -1),  _LIGHT),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.4, _DIVIDER),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story += [tc, Spacer(1, 0.25 * cm)]

    # 5. Case-by-Case Breakdown
    story.append(Paragraph("5. Case-by-Case Breakdown", s["H2"]))
    story.append(Paragraph(
        "What each method found on every individual test case.", s["Body"]
    ))
    story.append(Spacer(1, 0.15 * cm))

    for row in data["case_rows"]:
        cat_label = row["category"].replace("_", " ").title()
        expected_label = ", ".join(row["expected"]) if row["expected"] != ["none"] else "No issues expected"
        elems = [
            Paragraph(
                f"<b>{row['id']}</b> — {cat_label} | Expected: {expected_label}",
                s["BodyBold"]
            ),
            Paragraph("Rule-Based found:", s["Small"]),
        ]
        if row["baseline_issues"]:
            for issue in row["baseline_issues"]:
                _, _, label = _ISSUE_META.get(issue["type"], (_GRAY, _LGRAY, issue["type"].title()))
                elems.append(_p(f"  • <b>{label}:</b> {issue['description']}", s["Cell"]))
        else:
            elems.append(_p("  • No issues detected", s["CellGray"]))

        elems.append(Paragraph("AI (Groq) found:", s["Small"]))
        if row["llm_issues"]:
            for issue in row["llm_issues"]:
                _, _, label = _ISSUE_META.get(issue["type"], (_GRAY, _LGRAY, issue["type"].title()))
                elems.append(_p(f"  • <b>{label}:</b> {issue['description']}", s["Cell"]))
        else:
            elems.append(_p("  • No issues detected", s["CellGray"]))

        elems.append(Spacer(1, 0.15 * cm))
        story.append(KeepTogether(elems))

    # 6. Glossary
    story += _glossary(_GLOSSARY_BENCHMARK, s)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def render_pdf(data: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    s = _styles()
    story = []

    subtitle = (
        "Single transcript vs summary analysis"
        if data["mode"] == "single"
        else "Full benchmark run across all test cases"
    )
    story += [
        Paragraph("InfoGuard", s["AppTitle"]),
        Paragraph(subtitle, s["SubTitle"]),
        Paragraph(f"Generated: {data['generated_at']}", s["Small"]),
        HRFlowable(width="100%", thickness=1.5, color=_ACCENT, spaceAfter=12),
    ]

    if data["mode"] == "single":
        _render_single(data, story, s)
    else:
        _render_benchmark(data, story, s)

    doc.build(story)
    return output_path
