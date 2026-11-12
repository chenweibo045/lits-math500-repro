#!/usr/bin/env python3
"""Render the reproducibility report Markdown to a clean PDF with reportlab.
Supports: #-### headings, paragraphs, pipe tables, fenced code blocks,
bullet/numbered lists, bold/italic/inline-code rich text."""
import re
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable)

MD = sys.argv[1] if len(sys.argv) > 1 else "Reproducibility_Report.md"
OUT = sys.argv[2] if len(sys.argv) > 2 else "Reproducibility_Report.pdf"

NAVY = HexColor("#1F3864")
TEXT = HexColor("#1A1A1A")
MUTED = HexColor("#5A5A5A")
LIGHT = HexColor("#EEF2F9")

styles = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=17, leading=22, textColor=NAVY, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=NAVY, spaceBefore=12, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=TEXT, spaceBefore=8, spaceAfter=3),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13.6, textColor=TEXT, alignment=TA_JUSTIFY, spaceAfter=4),
    "li": ParagraphStyle("li", fontName="Helvetica", fontSize=9.5, leading=13.6, textColor=TEXT, leftIndent=14, spaceAfter=2),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8, leading=10.5, textColor=TEXT, backColor=LIGHT, borderPadding=4, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8.6, leading=11.4, textColor=TEXT),
    "cellh": ParagraphStyle("cellh", fontName="Helvetica-Bold", fontSize=8.6, leading=11.4, textColor=HexColor("#FFFFFF")),
    "meta": ParagraphStyle("meta", fontName="Helvetica", fontSize=9.5, leading=13.6, textColor=TEXT, spaceAfter=2),
}

def rich(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8.6">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<font color="#1F3864"><u>\1</u></font>', t)
    return t

def flush_table(tbl, story):
    if not tbl:
        return
    rows = []
    for i, row in enumerate(tbl):
        if re.match(r"^\s*:?-{2,}", row[0]):
            continue  # separator row
        cells = [c.strip() for c in row]
        st = styles["cellh"] if not rows else styles["cell"]
        rows.append([Paragraph(rich(c), st) for c in cells])
    if not rows:
        return
    ncol = len(rows[0])
    data = rows
    t = Table(data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), HexColor("#F4F7FC")]),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#C9D3E4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 5))

story = []
lines = open(MD, encoding="utf-8").read().splitlines()
tbl, in_code = [], False
first_h1 = True
for ln in lines:
    if ln.startswith("```"):
        in_code = not in_code
        continue
    if in_code:
        story.append(Paragraph(ln.replace("&", "&amp;").replace("<", "&lt;") or "&nbsp;", styles["code"]))
        continue
    if ln.strip().startswith("|"):
        cells = [c for c in ln.strip().strip("|").split("|")]
        tbl.append(cells)
        continue
    else:
        flush_table(tbl, story)
        tbl = []
    s = ln.rstrip()
    if not s.strip():
        story.append(Spacer(1, 3))
    elif s.startswith("# "):
        story.append(Paragraph(rich(s[2:]), styles["title"]))
        story.append(HRFlowable(width="100%", thickness=1.2, color=NAVY, spaceAfter=6))
    elif s.startswith("## "):
        story.append(Paragraph(rich(s[3:]), styles["h2"]))
    elif s.startswith("### "):
        story.append(Paragraph(rich(s[4:]), styles["h3"]))
    elif s.startswith("---"):
        story.append(Spacer(1, 4))
    elif re.match(r"^\s*[-*] ", s):
        story.append(Paragraph("• " + rich(re.sub(r"^\s*[-*] ", "", s)), styles["li"]))
    elif re.match(r"^\s*\d+\. ", s):
        story.append(Paragraph(rich(s.strip()), styles["li"]))
    elif s.startswith(">"):
        story.append(Paragraph(rich(s.lstrip("> ")), ParagraphStyle(
            "quote", parent=styles["body"], leftIndent=10, textColor=MUTED,
            borderColor=NAVY, borderWidth=0, borderPadding=0)))
    else:
        story.append(Paragraph(rich(s), styles["body"]))
flush_table(tbl, story)

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                      topMargin=16*mm, bottomMargin=16*mm,
                      title="FTEC5660 Reproducibility Work — LiTS on MATH500",
                      author="FTEC5660 Student")
doc.build(story)
print("wrote", OUT)
