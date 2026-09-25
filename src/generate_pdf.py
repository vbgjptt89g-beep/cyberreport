"""Convierte Markdown a un PDF compatible con las fuentes estándar de FPDF."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fpdf import FPDF

MARGIN = 18
MAX_REPORT_PAGES = 6
MAX_PUBLICATIONS_IN_PDF = 8
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
    line = line.rstrip()
    if len(line) > 500:
        line = line[:497] + "..."
    line = _core_font_text(line)

    if line.startswith("# "):
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(15, 15, 15)
        pdf.multi_cell(0, 9, line[2:])
        pdf.ln(2)
    elif line.startswith("## "):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 60, 110)
        pdf.multi_cell(0, 8, line[3:])
        pdf.ln(1)
    elif line.startswith(("- ", "* ")):
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.set_x(MARGIN + 4)
        pdf.multi_cell(0, 6.5, f"-  {line[2:]}")
    elif line == "":
        pdf.ln(2)
    else:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 6.5, line)


def _limit_publications(markdown: str, limit: int = MAX_PUBLICATIONS_IN_PDF) -> str:
    """Conserva el análisis y limita las publicaciones detalladas del PDF."""
    lines = markdown.splitlines()
    output: list[str] = []
    in_publications = False
    shown = 0
    omitted = 0

    for line in lines:
        if line.startswith("## "):
            if in_publications and omitted:
                output.append(f"Se omiten las demás publicaciones de esta sección para mantener el PDF en un máximo de seis páginas.")
            in_publications = "publicaciones consultadas" in line.casefold() or "registro completo de publicaciones" in line.casefold()
            shown = omitted = 0
            output.append(line)
            continue

        if in_publications and line.startswith("### "):
            if shown >= limit:
                omitted += 1
                continue
            shown += 1
        if in_publications and omitted:
            continue
        output.append(line)

    if in_publications and omitted:
        output.append(f"Se omiten las demás publicaciones de esta sección para mantener el PDF en un máximo de seis páginas.")
    return "\n".join(output)


def build_pdf(report_markdown: str, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prueba como máximo dos versiones y conserva seis páginas o menos.
    pdf = None
    for publication_limit in (MAX_PUBLICATIONS_IN_PDF, 0):
        print(f"Preparando PDF: hasta {publication_limit} publicaciones detalladas...", flush=True)
        compact_markdown = _limit_publications(report_markdown, publication_limit)
        candidate = ReportPDF()
        candidate.set_auto_page_break(auto=True, margin=18)
        candidate.set_margins(MARGIN, 16, MARGIN)
        candidate.add_page()
        for line in compact_markdown.splitlines():
            _write_markdown_line(candidate, line)
        pdf = candidate
        print(f"    -> Maquetación terminada: {candidate.page_no()} páginas.", flush=True)
        if candidate.page_no() <= MAX_REPORT_PAGES:
            break

    if pdf is None or pdf.page_no() > MAX_REPORT_PAGES:
        raise ValueError("El contenido principal excede el límite de seis páginas.")

    pdf.output(str(output_path))
    print("    -> Archivo PDF escrito correctamente.", flush=True)
    return output_path

