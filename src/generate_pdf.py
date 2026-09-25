"""Genera un boletín semanal de tecnología con noticias e ilustraciones."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from fpdf import FPDF

PAGE_W = 297
PAGE_H = 210
MARGIN = 10
LOGO_PATH = Path(__file__).resolve().parents[1] / "site" / "assets" / "logo-grupo-comidas-circular.png"
INK = (38, 42, 53)
INK_SOFT = (62, 72, 91)
RED = (211, 35, 47)
GOLD = (231, 163, 34)
TEAL = (24, 145, 111)
BLUE = (71, 126, 160)
CYAN = (74, 201, 210)
PURPLE = (137, 115, 210)
PALE = (255, 255, 255)
WHITE = (255, 255, 255)
TEXT = (48, 54, 64)
MUTED = (103, 111, 122)
BORDER = (222, 226, 230)
_REPLACEMENTS = str.maketrans({
    "—": "-", "–": "-", "−": "-", "‑": "-", "‘": "'", "’": "'",
    "“": '"', "”": '"', "…": "...", "•": "-", "\u00a0": " ",
})


class ReportPDF(FPDF):
    def header(self) -> None:
        pass

    def footer(self) -> None:
        pass


def _plain(text: str) -> str:
    text = text.translate(_REPLACEMENTS)
    text = re.sub(r"[*_]+", "", text)
    return " ".join(text.split()).encode("latin-1", errors="replace").decode("latin-1")


def _section_lines(markdown: str, heading: str) -> list[str]:
    selected = False
    result = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            if selected:
                break
            selected = heading in line.casefold()
            continue
        if selected:
            result.append(line)
    return result


def _first_paragraph(lines: list[str], default: str) -> str:
    for line in lines:
        line = _plain(line.strip())
        if line and not line.startswith(("-", "*", ">")):
            return line
    return default


def _truncate(text: str, limit: int) -> str:
    text = _plain(text)
    if len(text) <= limit:
        return text
    clipped = text[: limit - 3].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return (clipped or text[: limit - 3]) + "..."


def _write_text(pdf: ReportPDF, x: float, y: float, width: float, text: str,
                size: float = 8, color: tuple[int, int, int] = TEXT,
                bold: bool = False, line_height: float = 3.5,
                link: str | None = None) -> float:
    pdf.set_xy(x, y)
    pdf.set_font("Helvetica", "B" if bold else "", size)
    pdf.set_text_color(*color)
    wrapmode = "CHAR" if any(len(token) > 60 for token in text.split()) else "WORD"
    pdf.multi_cell(width, line_height, _plain(text), align="L", wrapmode=wrapmode, link=link or "")
    return pdf.get_y()


def _panel(pdf: ReportPDF, x: float, y: float, width: float, height: float,
           title: str, accent: tuple[int, int, int]) -> None:
    pdf.set_draw_color(*BORDER)
    pdf.set_fill_color(*WHITE)
    pdf.rect(x, y, width, height, style="DF")
    pdf.set_fill_color(*accent)
    pdf.rect(x, y, width, 9, style="F")
    pdf.rect(x, y + 5, width, 4, style="F")
    pdf.set_xy(x + 4, y + 1.4)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*WHITE)
    pdf.cell(width - 8, 6, _plain(title.upper()))


def _parse_publications(markdown: str) -> list[dict[str, str]]:
    lines = _section_lines(markdown, "noticias destacadas")
    publications: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in lines:
        if line.startswith("### "):
            if current:
                publications.append(current)
            current = {"title": _plain(line[4:]), "source": "", "date": "", "summary": "", "url": ""}
        elif current and line.startswith("- Fuente:"):
            current["source"] = _plain(line.partition(":")[2])
        elif current and line.startswith("- Fecha:"):
            current["date"] = _plain(line.partition(":")[2])
        elif current and line.startswith("- Resumen:"):
            current["summary"] = _plain(line.partition(":")[2])
        elif current and line.startswith("- Enlace:"):
            current["url"] = line.partition(":")[2].strip()
    if current:
        publications.append(current)
    return publications[:4]


def _parse_trends(markdown: str) -> list[str]:
    trends = []
    for line in _section_lines(markdown, "tendencias tecnológicas"):
        match = re.match(r"\s*[-*]\s*(.+)", line)
        if match:
            trends.append(_plain(match.group(1)))
    return trends[:3]


def _draw_header(pdf: ReportPDF) -> None:
    pdf.set_fill_color(*INK)
    pdf.rect(0, 0, PAGE_W, 34, style="F")
    pdf.set_fill_color(*RED)
    pdf.ellipse(10, 8, 16, 16, style="F")
    # Chip mark en lugar del escudo de ciberseguridad.
    pdf.set_draw_color(*WHITE)
    pdf.set_fill_color(*WHITE)
    pdf.rect(14, 12, 8, 8, style="DF")
    pdf.set_draw_color(*WHITE)
    for offset in (0, 2.5, 5):
        pdf.line(12.2, 13 + offset, 14, 13 + offset)
        pdf.line(22, 13 + offset, 23.8, 13 + offset)
        pdf.line(15.5 + offset, 10.2, 15.5 + offset, 12)
        pdf.line(15.5 + offset, 20, 15.5 + offset, 21.8)
    pdf.set_fill_color(*RED)
    pdf.rect(16.2, 14.2, 3.6, 3.6, style="F")
    pdf.set_xy(33, 7)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*WHITE)
    pdf.cell(180, 7, "BOLETÍN SEMANAL DE TECNOLOGÍA")
    pdf.set_xy(33, 17)
    pdf.set_font("Helvetica", "B", 9.2)
    pdf.set_text_color(245, 187, 59)
    pdf.cell(190, 6, "INNOVACIÓN - CIENCIA - DISPOSITIVOS Y SOFTWARE")
    if LOGO_PATH.exists():
        pdf.image(str(LOGO_PATH), x=250, y=4, w=25, h=25)
    pdf.set_xy(257, 29)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(220, 224, 230)
    pdf.cell(30, 3, f"{date.today():%d/%m/%Y}  |  1/1", align="R")


def _draw_story(pdf: ReportPDF, x: float, y: float, width: float,
                item: dict[str, str], index: int) -> None:
    accents = (RED, BLUE, TEAL, GOLD)
    accent = accents[(index - 1) % len(accents)]
    pdf.set_draw_color(*BORDER)
    pdf.set_fill_color(*WHITE)
    pdf.rect(x, y, width, 25.2, style="DF")
    pdf.set_fill_color(*accent)
    pdf.rect(x, y, 2, 25.2, style="F")
    _write_text(pdf, x + 5, y + 2.0, width - 10, _truncate(item.get("title", "Noticia destacada"), 130),
                8.1, INK, True, 3.7, item.get("url") or None)
    source = item.get("source", "Fuente tecnológica")
    published = item.get("date", "")
    _write_text(pdf, x + 5, y + 9.8, width - 10, f"{source}  |  {published}", 7.0, accent, True, 3.1)
    summary = item.get("summary") or "Consulta la publicación original para leer los detalles."
    _write_text(pdf, x + 5, y + 13.4, width - 10, _truncate(summary, 210), 7.2, MUTED, False, 3.25)


def _draw_ai_illustration(pdf: ReportPDF, x: float, y: float, width: float, height: float) -> None:
    pdf.set_fill_color(*INK)
    pdf.rect(x, y, width, height, style="F")
    cx, cy = x + width / 2, y + height / 2
    pdf.set_draw_color(69, 97, 123)
    pdf.set_line_width(0.65)
    for left, right in ((x + 6, cx - 7), (cx + 7, x + width - 6)):
        pdf.line(left, cy, right, cy)
        pdf.line(left + 2, y + 5, cx - 6, cy - 2)
        pdf.line(left + 2, y + height - 5, cx - 6, cy + 2)
    for nx, ny, color in ((x + 7, y + 4, CYAN), (x + 7, y + height - 6, GOLD),
                          (x + width - 9, y + 4, PURPLE), (x + width - 9, y + height - 6, CYAN)):
        pdf.set_fill_color(*color)
        pdf.ellipse(nx, ny, 3.5, 3.5, style="F")
    pdf.set_fill_color(48, 64, 84)
    pdf.set_draw_color(*CYAN)
    pdf.rect(cx - 8, cy - 7, 16, 14, style="DF")
    pdf.set_fill_color(*GOLD)
    pdf.rect(cx - 4, cy - 3.5, 8, 7, style="F")
    pdf.set_draw_color(*CYAN)
    pdf.set_line_width(0.7)
    for offset in (-5, 0, 5):
        pdf.line(cx - 11, cy + offset, cx - 8, cy + offset)
        pdf.line(cx + 8, cy + offset, cx + 11, cy + offset)
    pdf.set_line_width(0.2)


def _draw_device_illustration(pdf: ReportPDF, x: float, y: float, width: float, height: float) -> None:
    pdf.set_fill_color(230, 241, 246)
    pdf.rect(x, y, width, height, style="F")
    # Portátil con panel de aplicaciones.
    monitor_x, monitor_y = x + 12, y + 3
    pdf.set_fill_color(35, 43, 56)
    pdf.rect(monitor_x, monitor_y, 33, height - 7, style="F")
    pdf.set_fill_color(249, 251, 252)
    pdf.rect(monitor_x + 2, monitor_y + 2, 29, height - 11, style="F")
    pdf.set_fill_color(*BLUE)
    pdf.rect(monitor_x + 4, monitor_y + 4, 10, 2, style="F")
    pdf.set_fill_color(*TEAL)
    pdf.rect(monitor_x + 4, monitor_y + 9, 20, 1.3, style="F")
    pdf.set_fill_color(*GOLD)
    pdf.rect(monitor_x + 4, monitor_y + 12, 14, 1.3, style="F")
    pdf.set_fill_color(128, 145, 161)
    pdf.polygon([(monitor_x + 12, y + height - 4), (monitor_x + 22, y + height - 4),
                 (monitor_x + 25, y + height - 2), (monitor_x + 9, y + height - 2)], style="F")
    # Teléfono y reloj inteligente.
    phone_x = x + width - 28
    pdf.set_fill_color(35, 43, 56)
    pdf.rect(phone_x, y + 3, 12, height - 5, style="F")
    pdf.set_fill_color(*WHITE)
    pdf.rect(phone_x + 1.4, y + 5, 9.2, height - 10, style="F")
    pdf.set_fill_color(*RED)
    pdf.ellipse(phone_x + 4.2, y + height - 4.4, 3, 1.5, style="F")
    pdf.set_fill_color(*PURPLE)
    pdf.ellipse(x + width - 11, y + 8, 6, 6, style="F")
    pdf.set_fill_color(*WHITE)
    pdf.ellipse(x + width - 9.4, y + 9.5, 2.8, 2.8, style="F")


def _draw_space_illustration(pdf: ReportPDF, x: float, y: float, width: float, height: float) -> None:
    pdf.set_fill_color(31, 39, 57)
    pdf.rect(x, y, width, height, style="F")
    for sx, sy, size, color in ((x + 8, y + 5, 1.8, WHITE), (x + 21, y + 13, 1.3, GOLD),
                                (x + width - 8, y + 5, 1.6, CYAN), (x + width - 19, y + 13, 1.2, WHITE)):
        pdf.set_fill_color(*color)
        pdf.ellipse(sx, sy, size, size, style="F")
    # Planeta y trayectoria.
    pdf.set_fill_color(51, 114, 164)
    pdf.ellipse(x + width - 31, y + 3, 18, 18, style="F")
    pdf.set_fill_color(*TEAL)
    pdf.ellipse(x + width - 27, y + 7, 5, 3.5, style="F")
    pdf.set_fill_color(*GOLD)
    pdf.ellipse(x + width - 18, y + 12, 4, 2.5, style="F")
    # Satélite central con paneles solares.
    cx, cy = x + width * 0.45, y + height * 0.52
    pdf.set_fill_color(*GOLD)
    pdf.rect(cx - 17, cy - 4, 10, 8, style="F")
    pdf.rect(cx + 7, cy - 4, 10, 8, style="F")
    pdf.set_fill_color(68, 179, 190)
    pdf.rect(cx - 5, cy - 6, 10, 12, style="F")
    pdf.set_draw_color(*WHITE)
    pdf.set_line_width(0.7)
    pdf.line(cx, cy - 6, cx + 3, cy - 9)
    pdf.line(cx + 3, cy - 9, cx + 7, cy - 9)
    pdf.set_line_width(0.2)


def _draw_technology_panel(pdf: ReportPDF, markdown: str) -> None:
    x, y, width = 188, 64, 99
    _panel(pdf, x, y, width, 115, "Tecnología en imágenes", PURPLE)
    topics = [
        ("IA Y SOFTWARE", "infografia-chip.jpg", "Jensen Huang, referente de NVIDIA y de la IA.", "Xataka · retrato editorial", "https://www.xataka.com/empresas-y-economia/no-puedes-pasar-dia-recibir-alguna-critica-modelo-liderazgo-jensen-huang-que-no-da-tregua-a-sus-empleados"),
        ("DISPOSITIVOS", "infografia-dispositivos.jpg", "Teléfono y portátil en un espacio de trabajo.", "Dextar Vision · Unsplash", "https://unsplash.com/photos/a-close-up-of-a-cell-phone-on-a-keyboard-zWifu7m5nJA"),
        ("EXPLORACIÓN ESPACIAL", "infografia-espacio.jpg", "El telescopio Hubble sobre la Tierra.", "NASA · Unsplash", "https://unsplash.com/photos/the-space-shuttle-is-flying-over-the-earth-WmbePYToF6c"),
    ]
    row_y = 76
    for caption, filename, detail, credit, source_url in topics:
        image_x, image_y, image_w, image_h = x + 5, row_y, 39, 27
        image_path = Path(__file__).resolve().parents[1] / "site" / "assets" / filename
        if image_path.exists():
            pdf.image(str(image_path), x=image_x, y=image_y, w=image_w, h=image_h)
        text_x, text_w = x + 47, width - 52
        _write_text(pdf, text_x, row_y + 1, text_w, caption, 6.3, INK, True, 2.7)
        _write_text(pdf, text_x, row_y + 5, text_w, detail, 6.0, MUTED, False, 2.6)
        _write_text(pdf, text_x, row_y + 20.5, text_w, f"Foto: {credit}", 5.6, BLUE, True, 2.4, source_url)
        row_y += 34

def _draw_page(pdf: ReportPDF, markdown: str) -> None:
    summary = _first_paragraph(
        _section_lines(markdown, "panorama semanal"),
        "Un repaso de novedades de inteligencia artificial, dispositivos, software, ciencia e innovación.",
    )
    publications = _parse_publications(markdown)
    pdf.set_fill_color(*PALE)
    pdf.rect(0, 34, PAGE_W, PAGE_H - 34, style="F")

    _panel(pdf, 10, 39, 277, 21, "Panorama de la semana", BLUE)
    _write_text(pdf, 15, 50, 267, _truncate(summary, 310), 8.1, TEXT, False, 3.6)

    _panel(pdf, 10, 64, 172, 115, "Noticias destacadas", GOLD)
    if publications:
        row_y = 75
        for index, item in enumerate(publications, 1):
            _draw_story(pdf, 15, row_y, 162, item, index)
            row_y += 26
    else:
        _write_text(pdf, 16, 78, 160, "No hay noticias recientes disponibles para esta edición. Revisa el sitio web cuando se actualicen las fuentes.", 9, TEXT)

    _draw_technology_panel(pdf, markdown)

    pdf.set_fill_color(*INK)
    pdf.rect(10, 185, 277, 15, style="F")
    pdf.set_xy(16, 189)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(245, 187, 59)
    pdf.cell(100, 6, "TECNOLOGÍA, CIENCIA E INNOVACIÓN")
    pdf.set_xy(170, 189)
    pdf.set_font("Helvetica", "", 8.3)
    pdf.set_text_color(*WHITE)
    pdf.cell(110, 6, "Novedades explicadas con sus fuentes originales.", align="R")


def build_pdf(report_markdown: str, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = ReportPDF(orientation="L", format="A4")
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    pdf.set_auto_page_break(auto=False, margin=MARGIN)
    pdf.add_page()
    _draw_header(pdf)
    _draw_page(pdf, report_markdown)
    pdf.output(str(output_path))
    print("    -> Boletín tecnológico de una página escrito correctamente.", flush=True)
    return output_path







