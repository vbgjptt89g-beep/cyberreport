"""Convierte Markdown a un PDF compatible con las fuentes estándar de FPDF."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fpdf import FPDF

MARGIN = 18
_CORE_FONT_REPLACEMENTS = str.maketrans({
    "—": "-", "–": "-", "−": "-", "‑": "-",
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "…": "...", "•": "-", "\u00a0": " ",
})


def _core_font_text(text: str) -> str:
    """Preserva español latino y reemplaza símbolos que Helvetica no codifica."""
    translated = text.translate(_CORE_FONT_REPLACEMENTS)
    return translated.encode("latin-1", errors="replace").decode("latin-1")


class ReportPDF(FPDF):
    def header(self) -> None:  # noqa: D102
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(20, 20, 20)
        self.cell(0, 10, "Informe Semanal de Ciberseguridad", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, f"Generado automáticamente el {date.today():%d/%m/%Y}", ln=True, align="C")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(MARGIN, self.get_y(), 210 - MARGIN, self.get_y())
        self.ln(6)

    def footer(self) -> None:  # noqa: D102
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


def _write_markdown_line(pdf: ReportPDF, line: str) -> None:
    line = _core_font_text(line.rstrip())

    if line.startswith("# "):
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(15, 15, 15)
        pdf.multi_cell(0, 9, line[2:], wrapmode="CHAR")
        pdf.ln(2)
    elif line.startswith("## "):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 60, 110)
        pdf.multi_cell(0, 8, line[3:], wrapmode="CHAR")
        pdf.ln(1)
    elif line.startswith(("- ", "* ")):
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.set_x(MARGIN + 4)
        pdf.multi_cell(0, 6.5, f"-  {line[2:]}", wrapmode="CHAR")
    elif line == "":
        pdf.ln(2)
    else:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 6.5, line, wrapmode="CHAR")


def build_pdf(report_markdown: str, output_path: str | Path) -> Path:
    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(MARGIN, 16, MARGIN)
    pdf.add_page()

    for line in report_markdown.splitlines():
        _write_markdown_line(pdf, line)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path
