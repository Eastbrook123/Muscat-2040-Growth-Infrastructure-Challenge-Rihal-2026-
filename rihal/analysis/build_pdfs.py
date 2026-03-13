from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(r"c:\Users\musafa\OneDrive\Desktop\rihal")
OUT = ROOT / "outputs"


def md_lines_to_flowables(lines: list[str], title: str) -> list:
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], spaceAfter=6)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceAfter=4)
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], spaceAfter=3)
    body = ParagraphStyle("Body", parent=styles["BodyText"], leading=14, spaceAfter=6)
    mono = ParagraphStyle("Mono", parent=styles["BodyText"], fontName="Courier", fontSize=9.5, leading=11.5, spaceAfter=6)

    story = [Paragraph(title, h1), Spacer(1, 4 * mm)]

    in_code = False
    code_buf: list[str] = []
    for raw in lines:
        line = raw.rstrip("\n")
        if line.strip().startswith("```"):
            if in_code:
                story.append(Paragraph("<br/>".join([c.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for c in code_buf]), mono))
                story.append(Spacer(1, 2 * mm))
                code_buf = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_buf.append(line)
            continue

        if line.startswith("# "):
            story.append(Paragraph(line[2:], h1))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], h2))
        elif line.startswith("### "):
            story.append(Paragraph(line[4:], h3))
        elif line.startswith("- "):
            story.append(Paragraph(f"• {line[2:]}", body))
        elif line.strip() == "":
            story.append(Spacer(1, 2 * mm))
        else:
            safe = (
                line.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            story.append(Paragraph(safe, body))
    return story


def md_to_pdf(md_path: Path, pdf_path: Path, title: str) -> None:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=title,
    )
    story = md_lines_to_flowables(lines, title=title)
    doc.build(story)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    md_to_pdf(
        OUT / "Muscat_2040_Executive_Summary.md",
        OUT / "Muscat_2040_Executive_Summary.pdf",
        "Muscat 2040 — Executive Summary",
    )
    md_to_pdf(
        OUT / "Muscat_2040_Technical_Appendix.md",
        OUT / "Muscat_2040_Technical_Appendix_and_Logic.pdf",
        "Muscat 2040 — Technical Appendix & Calculation Logic",
    )
    print("Wrote PDFs to:", OUT)


if __name__ == "__main__":
    main()

