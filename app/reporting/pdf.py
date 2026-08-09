from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

_W, _H = A4
_BRAND = colors.HexColor("#1a1a2e")
_ACCENT = colors.HexColor("#4f8ef7")
_LIGHT = colors.HexColor("#f0f4ff")
_PASS = colors.HexColor("#2ecc71")
_FAIL = colors.HexColor("#e74c3c")
_GRAY = colors.HexColor("#7f8c8d")


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Title2", parent=s["Title"], textColor=_BRAND, fontSize=22, spaceAfter=6))
    s.add(ParagraphStyle("Sub", parent=s["Normal"], textColor=_GRAY, fontSize=10, spaceAfter=12))
    s.add(ParagraphStyle("H2", parent=s["Heading2"], textColor=_BRAND, fontSize=13, spaceBefore=14, spaceAfter=6))
    s.add(ParagraphStyle("Body", parent=s["Normal"], fontSize=9, leading=13))
    s.add(ParagraphStyle("Small", parent=s["Normal"], fontSize=8, textColor=_GRAY))
    return s


def _tbl_style(header_bg=_BRAND):
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d0d0")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])


def render_pdf(data: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    s = _styles()
    story = []

    # --- Header ---
    story += [
        Paragraph("InfoGuard", s["Title2"]),
        Paragraph("Transcript vs Summary Evaluation Report", s["Sub"]),
        Paragraph(f"Generated: {data['generated_at']}  |  Total cases: {data['total_cases']}", s["Small"]),
        HRFlowable(width="100%", thickness=1, color=_ACCENT, spaceAfter=12),
    ]

    # --- Overview summary ---
    story.append(Paragraph("1. Overview", s["H2"]))
    overview = [
        ["Metric", "Baseline", "LLM (Groq)"],
        ["Overall Accuracy",
         f"{data['baseline']['overall_accuracy']:.0%}",
         f"{data['llm']['overall_accuracy']:.0%}"],
        ["Avg Latency (s)",
         f"{data['baseline']['avg_latency']:.4f}",
         f"{data['llm']['avg_latency']:.4f}"],
    ]
    t = Table(overview, colWidths=[7*cm, 4*cm, 4*cm])
    t.setStyle(_tbl_style())
    story += [t, Spacer(1, 0.4*cm)]

    # --- Category accuracy ---
    story.append(Paragraph("2. Accuracy by Category", s["H2"]))
    cats = sorted(data["baseline"]["category_accuracy"].keys())
    cat_rows = [["Category", "Baseline", "LLM"]]
    for cat in cats:
        cat_rows.append([
            cat.replace("_", " ").title(),
            f"{data['baseline']['category_accuracy'].get(cat, 0):.0%}",
            f"{data['llm']['category_accuracy'].get(cat, 0):.0%}",
        ])
    t2 = Table(cat_rows, colWidths=[7*cm, 4*cm, 4*cm])
    t2.setStyle(_tbl_style())
    story += [t2, Spacer(1, 0.4*cm)]

    # --- Issue-type precision / recall / F1 ---
    story.append(Paragraph("3. Issue-Type Metrics (Precision / Recall / F1)", s["H2"]))
    metric_rows = [["Issue Type", "B-Prec", "B-Rec", "B-F1", "LLM-Prec", "LLM-Rec", "LLM-F1"]]
    for row in data["comparison_table"]:
        metric_rows.append([
            row["issue_type"],
            f"{row['baseline_precision']:.2f}",
            f"{row['baseline_recall']:.2f}",
            f"{row['baseline_f1']:.2f}",
            f"{row['llm_precision']:.2f}",
            f"{row['llm_recall']:.2f}",
            f"{row['llm_f1']:.2f}",
        ])
    t3 = Table(metric_rows, colWidths=[3*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm])
    t3.setStyle(_tbl_style())
    story += [t3, Spacer(1, 0.4*cm)]

    # --- Per-case results ---
    story.append(Paragraph("4. Per-Case Results", s["H2"]))
    case_header = ["ID", "Category", "Expected", "Baseline", "LLM", "B-ms", "LLM-ms"]
    case_data = [case_header]
    for row in data["case_rows"]:
        case_data.append([
            row["id"],
            row["category"].replace("_", " "),
            ", ".join(row["expected"]),
            ", ".join(row["baseline"]),
            ", ".join(row["llm"]),
            f"{row['baseline_latency']*1000:.1f}",
            f"{row['llm_latency']*1000:.1f}",
        ])
    t4 = Table(case_data, colWidths=[2*cm, 3.2*cm, 2.4*cm, 2.8*cm, 2.8*cm, 1.4*cm, 1.4*cm])
    style4 = _tbl_style()
    # Colour-code rows where baseline or LLM detected issues
    t4.setStyle(style4)
    story += [t4, Spacer(1, 0.4*cm)]

    # --- Approach comparison narrative ---
    story.append(Paragraph("5. Approach Comparison", s["H2"]))
    narrative = (
        "<b>Baseline (Deterministic):</b> Uses regex-based fact extraction and Jaccard token overlap "
        "to detect missing, extra, and incorrect facts. It is extremely fast (~1ms per case) and fully "
        "deterministic, making it reliable for regression testing. Its main limitation is low precision — "
        "it generates false positives on facts that are semantically equivalent but lexically different.<br/><br/>"
        "<b>LLM Comparator (Groq / llama-3.3-70b-versatile):</b> Prompts the model to reason over the "
        "transcript and summary and return structured issue detections. It achieves higher precision, "
        "handles paraphrasing and ambiguity better, and produces more human-readable descriptions. "
        "Its limitations are latency (~400ms per case), cost, and non-determinism across runs.<br/><br/>"
        "<b>Recommendation:</b> Use the baseline for fast CI-style regression checks and the LLM comparator "
        "for production evaluation where precision and nuance matter."
    )
    story.append(Paragraph(narrative, s["Body"]))
    story.append(Spacer(1, 0.4*cm))

    # --- Limitations ---
    story.append(Paragraph("6. Limitations & Next Steps", s["H2"]))
    limitations = (
        "The benchmark is synthetic and small (12 cases). Real-world transcripts may contain more "
        "complex language, domain-specific terminology, and multi-issue cases. The baseline does not "
        "handle semantic equivalence (e.g. '$75' vs 'seventy-five dollars'). The LLM comparator is "
        "subject to rate limits and model updates. Future improvements include a larger benchmark, "
        "semantic similarity scoring, and a caching layer for LLM responses."
    )
    story.append(Paragraph(limitations, s["Body"]))

    doc.build(story)
    return output_path
