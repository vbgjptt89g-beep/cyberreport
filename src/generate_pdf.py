"""Genera un informe semanal de ciberseguridad en formato infografía."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from fpdf import FPDF

PAGE_W = 297
PAGE_H = 210
MARGIN = 10
MAX_PUBLICATIONS_IN_PDF = 8
LOGO_PATH = Path(__file__).resolve().parents[1] / "site" / "assets" / "cybernews-logo.jpeg"

INK = (38, 42, 53)
INK_SOFT = (58, 65, 80)
RED = (211, 35, 47)
GOLD = (231, 163, 34)
TEAL = (24, 145, 111)
BLUE = (71, 126, 160)
PALE = (244, 246, 248)
WHITE = (255, 255, 255)
TEXT = (48, 54, 64)
MUTED = (103, 111, 122)
BORDER = (222, 226, 230)
_CORE_FONT_REPLACEMENTS = str.maketrans({
    "—": "-", "–": "-", "−": "-", "‑": "-",
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "…": "...", "•": "-", "\u00a0": " ",
})


class ReportPDF(FPDF):
    def header(self) -> None:
        pass

    def footer(self) -> None:
        pass


def _plain(text: str) -> str:
    text = text.translate(_CORE_FONT_REPLACEMENTS)
    text = re.sub(r"[*_]+", "", text)
    return " ".join(text.split()).encode("latin-1", errors="replace").decode("latin-1")


def _section_lines(markdown: str, heading: str) -> list[str]:
    selected = False
    result: list[str] = []
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
        if line and not line.startswith(("-", "*", ">")) and not re.match(r"^\d+[.)]\s", line):
            return line
    return default


def _truncate(text: str, limit: int) -> str:
    text = _plain(text)
    if len(text) <= limit:
        return text
    clipped = text[: limit - 3].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return (clipped or text[: limit - 3]) + "..."


def _write_text(
    pdf: ReportPDF,
    x: float,
    y: float,
    width: float,
    text: str,
    size: float = 9,
    color: tuple[int, int, int] = TEXT,
    bold: bool = False,
    line_height: float = 4.2,
    link: str | None = None,
) -> float:
    text = _plain(text)
    pdf.set_xy(x, y)
    pdf.set_font("Helvetica", "B" if bold else "", size)
    pdf.set_text_color(*color)
    if link and "\n" not in text:
        pdf.cell(width, line_height, text, link=link, new_x="LEFT", new_y="NEXT")
        return pdf.get_y()
    wrapmode = "CHAR" if any(len(token) > 60 for token in text.split()) else "WORD"
    pdf.multi_cell(width, line_height, text, align="L", wrapmode=wrapmode)
    return pdf.get_y()


def _panel(
    pdf: ReportPDF,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    accent: tuple[int, int, int],
) -> None:
    pdf.set_draw_color(*BORDER)
    pdf.set_fill_color(*WHITE)
    pdf.rect(x, y, width, height, style="DF")
    pdf.set_fill_color(*accent)
    pdf.rect(x, y, width, 9, style="F")
    pdf.rect(x, y + 5, width, 4, style="F")
    pdf.set_xy(x + 4, y + 1.4)
    pdf.set_font("Helvetica", "B", 9.3)
    pdf.set_text_color(*WHITE)
    pdf.cell(width - 8, 6, _plain(title.upper()), new_x="LEFT", new_y="NEXT")


def _draw_shield(pdf: ReportPDF, x: float, y: float, size: float, color: tuple[int, int, int]) -> None:
    points = [
        (x + size * 0.50, y),
        (x + size * 0.90, y + size * 0.16),
        (x + size * 0.84, y + size * 0.62),
        (x + size * 0.50, y + size),
        (x + size * 0.16, y + size * 0.62),
        (x + size * 0.10, y + size * 0.16),
        (x + size * 0.50, y),
    ]
    pdf.set_draw_color(*color)
    pdf.set_line_width(0.8)
    for first, second in zip(points, points[1:]):
        pdf.line(first[0], first[1], second[0], second[1])
    pdf.set_line_width(0.2)
    pdf.line(x + size * 0.31, y + size * 0.49, x + size * 0.45, y + size * 0.63)
    pdf.line(x + size * 0.45, y + size * 0.63, x + size * 0.70, y + size * 0.34)


def _draw_device_illustration(pdf: ReportPDF, x: float, y: float) -> None:
    """Escena ilustrada: estación de trabajo, móvil y escudo frente a amenazas."""
    # Fondo oscuro y halos de color, inspirado en una infografía editorial.
    pdf.set_fill_color(*INK)
    pdf.rect(x, y, 71, 45, style="F")
    pdf.set_fill_color(50, 58, 74)
    pdf.ellipse(x + 21, y + 3, 35, 35, style="F")
    pdf.set_draw_color(80, 94, 112)
    pdf.set_line_width(0.45)
    pdf.ellipse(x + 24, y + 4, 29, 29, style="D")

    # Ventana de seguridad dentro del monitor.
    pdf.set_draw_color(91, 105, 124)
    pdf.set_fill_color(29, 34, 45)
    pdf.rect(x + 4, y + 13, 31, 21, style="DF")
    pdf.set_fill_color(232, 239, 244)
    pdf.rect(x + 5.8, y + 15, 27.4, 16.2, style="F")
    pdf.set_fill_color(*RED)
    pdf.ellipse(x + 7.5, y + 16.4, 2.2, 2.2, style="F")
    pdf.set_fill_color(*GOLD)
    pdf.ellipse(x + 10.7, y + 16.4, 2.2, 2.2, style="F")
    pdf.set_fill_color(*TEAL)
    pdf.ellipse(x + 13.9, y + 16.4, 2.2, 2.2, style="F")
    pdf.set_draw_color(190, 202, 211)
    pdf.set_line_width(0.7)
    pdf.line(x + 8, y + 21, x + 18, y + 21)
    pdf.line(x + 8, y + 24, x + 15, y + 24)
    pdf.line(x + 8, y + 27, x + 19, y + 27)
    pdf.set_fill_color(255, 230, 230)
    pdf.ellipse(x + 23.5, y + 21, 6.5, 6.5, style="F")
    pdf.set_xy(x + 25.2, y + 22.2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*RED)
    pdf.cell(3, 4, "!")
    pdf.set_fill_color(144, 158, 172)
    pdf.polygon([(x + 17, y + 34), (x + 22, y + 34), (x + 24, y + 38), (x + 15, y + 38)], style="F")
    pdf.rect(x + 11, y + 38, 17, 1.5, style="F")

    # Teléfono con una alerta de acceso protegido.
    pdf.set_draw_color(100, 111, 127)
    pdf.set_fill_color(19, 23, 32)
    pdf.rect(x + 54, y + 16, 11, 23, style="DF")
    pdf.set_fill_color(239, 243, 246)
    pdf.rect(x + 55.3, y + 18, 8.4, 18.5, style="F")
    pdf.set_fill_color(*BLUE)
    pdf.rect(x + 56.5, y + 20, 5.8, 1.2, style="F")
    pdf.set_fill_color(219, 231, 239)
    pdf.rect(x + 56.5, y + 23, 5.8, 1, style="F")
    pdf.rect(x + 56.5, y + 25.5, 4.2, 1, style="F")
    pdf.set_fill_color(*GOLD)
    pdf.ellipse(x + 58.5, y + 37, 2, 1, style="F")

    # Pequeño mensaje sospechoso flotando sobre el monitor.
    pdf.set_fill_color(255, 245, 224)
    pdf.set_draw_color(*GOLD)
    pdf.rect(x + 5, y + 4, 14, 8, style="DF")
    pdf.set_draw_color(*RED)
    pdf.line(x + 5.5, y + 4.8, x + 12, y + 9)
    pdf.line(x + 18.5, y + 4.8, x + 12, y + 9)
    pdf.set_fill_color(*RED)
    pdf.ellipse(x + 15.5, y + 2, 5, 5, style="F")
    pdf.set_xy(x + 16.4, y + 2.2)
    pdf.set_font("Helvetica", "B", 6)
    pdf.set_text_color(*WHITE)
    pdf.cell(3, 4, "!")

    # Escudo en primer plano, con volumen, borde dorado y candado blanco.
    shield = [
        (x + 42, y + 5), (x + 52, y + 9), (x + 50, y + 25),
        (x + 42, y + 34), (x + 34, y + 25), (x + 32, y + 9),
    ]
    pdf.set_fill_color(20, 24, 34)
    pdf.polygon([(px + 1.2, py + 1.5) for px, py in shield], style="F")
    pdf.set_fill_color(*RED)
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(1.1)
    pdf.polygon(shield, style="DF")
    inner = [
        (x + 42, y + 8), (x + 49, y + 11), (x + 47.5, y + 24),
        (x + 42, y + 30), (x + 36.5, y + 24), (x + 35, y + 11),
    ]
    pdf.set_fill_color(231, 49, 62)
    pdf.set_draw_color(231, 49, 62)
    pdf.polygon(inner, style="F")
    pdf.set_draw_color(*WHITE)
    pdf.set_line_width(1.25)
    pdf.ellipse(x + 38, y + 15, 8, 9, style="D")
    pdf.set_fill_color(*WHITE)
    pdf.rect(x + 36.5, y + 19, 11, 8, style="F")
    pdf.set_fill_color(*RED)
    pdf.ellipse(x + 41, y + 21, 2, 2, style="F")
    pdf.set_fill_color(*WHITE)
    pdf.rect(x + 41.7, y + 22.5, 0.6, 2.1, style="F")
    pdf.set_line_width(0.2)


def _parse_publications(markdown: str) -> list[dict[str, str]]:
    lines = _section_lines(markdown, "publicaciones consultadas")
    publications: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in lines:
        if line.startswith("### "):
            title = _plain(line[4:])
            if "referencias oficiales" in title.casefold():
                if current:
                    publications.append(current)
                current = None
                continue
            if current:
                publications.append(current)
            current = {"title": title, "source": "", "date": "", "summary": "", "url": ""}
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
    return publications


def _parse_recommendations(markdown: str) -> list[str]:
    lines = _section_lines(markdown, "recomendaciones principales")
    recommendations: list[str] = []
    for line in lines:
        match = re.match(r"\s*(?:\d+[.)]\s*|[-*]\s*)(.+)", line)
        if match:
            text = _plain(match.group(1))
            if text:
                recommendations.append(text)
    return recommendations[:4]


def _draw_header(pdf: ReportPDF, title: str, subtitle: str, page_number: int) -> None:
    pdf.set_fill_color(*INK)
    pdf.rect(0, 0, PAGE_W, 34, style="F")
    pdf.set_fill_color(*RED)
    pdf.ellipse(10, 8, 16, 16, style="F")
    _draw_shield(pdf, 13.3, 11, 9.5, WHITE)
    pdf.set_xy(33, 7)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*WHITE)
    pdf.cell(180, 7, _plain(title.upper()), new_x="LEFT", new_y="NEXT")
    pdf.set_xy(33, 17)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(245, 187, 59)
    pdf.cell(190, 6, _truncate(subtitle.upper(), 70), new_x="LEFT", new_y="NEXT")
    pdf.set_fill_color(*WHITE)
    pdf.rect(238, 5, 49, 24, style="F")
    if LOGO_PATH.exists():
        pdf.image(str(LOGO_PATH), x=240, y=7, w=45, h=20, keep_aspect_ratio=True)
    pdf.set_xy(257, 29)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(220, 224, 230)
    pdf.cell(30, 3, f"{date.today():%d/%m/%Y}  |  {page_number}/2", align="R")




def _draw_page_one(pdf: ReportPDF, markdown: str, publications: list[dict[str, str]]) -> None:
    summary = _first_paragraph(
        _section_lines(markdown, "resumen ejecutivo"),
        "Consulta las publicaciones y aplica recomendaciones defensivas para proteger tus cuentas y dispositivos.",
    )
    threat = _first_paragraph(
        _section_lines(markdown, "amenazas y vulnerabilidades destacadas"),
        "No se atribuyen amenazas específicas sin evidencia suficiente. Revisa las fuentes originales.",
    )
    recommendations = _parse_recommendations(markdown)
    if not recommendations:
        recommendations = [
            "Activa MFA en correo y cuentas administrativas.",
            "Instala actualizaciones de seguridad disponibles.",
            "Mantén copias de seguridad y prueba restaurarlas.",
            "Verifica mensajes inesperados antes de abrir enlaces.",
        ]

    pdf.set_fill_color(*PALE)
    pdf.rect(0, 34, PAGE_W, PAGE_H - 34, style="F")

    _panel(pdf, 10, 42, 74, 48, "Panorama de la semana", BLUE)
    _write_text(pdf, 14, 55, 66, _truncate(summary, 175), 9.2, TEXT, line_height=4.4)

    _panel(pdf, 10, 96, 74, 83, "Riesgo a vigilar", RED)
    pdf.set_fill_color(255, 240, 220)
    pdf.ellipse(15, 109, 13, 13, style="F")
    pdf.set_xy(18.9, 111.7)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*GOLD)
    pdf.cell(5, 6, "!")
    _write_text(pdf, 32, 108, 47, _truncate(threat, 185), 8.5, TEXT, line_height=4.1)
    pdf.set_xy(15, 162)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(*RED)
    pdf.cell(62, 4, "DETENTE - VERIFICA - REPORTA")

    _panel(pdf, 90, 42, 112, 137, "Acciones prioritarias", GOLD)
    row_y = 54
    for index, recommendation in enumerate(recommendations, 1):
        accent = (RED, BLUE, TEAL, GOLD)[(index - 1) % 4]
        pdf.set_fill_color(*accent)
        pdf.ellipse(96, row_y + 1, 9, 9, style="F")
        pdf.set_xy(96, row_y + 2.2)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*WHITE)
        pdf.cell(9, 4, str(index), align="C")
        _write_text(pdf, 109, row_y, 87, _truncate(recommendation, 110), 8.8, TEXT, bold=True, line_height=4.1)
        if index < len(recommendations):
            pdf.set_draw_color(*BORDER)
            pdf.line(96, row_y + 23, 196, row_y + 23)
        row_y += 31

    _panel(pdf, 208, 42, 79, 137, "Protege tu día a día", TEAL)
    _draw_device_illustration(pdf, 212, 56)
    pdf.set_draw_color(*BORDER)
    pdf.line(213, 105, 282, 105)
    quick_tips = [
        ("1", "No abras enlaces inesperados."),
        ("2", "Confirma al remitente por otro canal."),
        ("3", "Reporta mensajes sospechosos."),
    ]
    tip_y = 111
    for number, tip in quick_tips:
        pdf.set_fill_color(*TEAL)
        pdf.ellipse(214, tip_y, 7, 7, style="F")
        pdf.set_xy(214, tip_y + 1.5)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*WHITE)
        pdf.cell(7, 4, number, align="C")
        _write_text(pdf, 224, tip_y - 0.2, 57, tip, 7.8, TEXT, line_height=3.6)
        tip_y += 21

    pdf.set_fill_color(*INK)
    pdf.rect(10, 185, 277, 15, style="F")
    pdf.set_xy(16, 189)
    pdf.set_font("Helvetica", "B", 9.3)
    pdf.set_text_color(245, 187, 59)
    pdf.cell(80, 6, "PAUSA. VERIFICA. REPORTA.")
    pdf.set_xy(170, 189)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*WHITE)
    pdf.cell(110, 6, "La seguridad comienza con una decisión informada.", align="R")


def _spanish_publication(item: dict[str, str]) -> tuple[str, str]:
    """Devuelve títulos y extractos breves en español, incluso sin una API de traducción."""
    original = item.get("title", "").strip()
    key = original.casefold()
    translated: list[tuple[str, str, str]] = [
        ("compromised github actions", "Acciones de GitHub comprometidas vuelven a ejecutar malware Mini Shai-Hulud", "Se deshabilitaron nuevamente acciones de GitHub comprometidas que habían vuelto a estar disponibles. Verifica las dependencias y revisa los avisos de seguridad de tus repositorios."),
        ("pamstealer", "PamStealer refuerza el cifrado y la persistencia de su malware para macOS", "Investigadores detectaron una nueva versión de PamStealer con cambios en la entrega y recuperación de su carga maliciosa. Evita instaladores y archivos de origen dudoso."),
        ("soc doesn't need", "El centro de operaciones de seguridad no debe empezar de cero con cada alerta", "El artículo explica cómo la inteligencia artificial puede facilitar que los atacantes repitan intentos fallidos. Correlacionar alertas y contexto ayuda a detectar esa actividad."),
        ("bitget says", "Bitget reporta un robo de 351,6 millones de dólares tras una intrusión", "Bitget informó de transferencias no autorizadas desde algunas billeteras activas y tibias. La empresa indicó que sus billeteras frías y la mayoría de los activos no se vieron afectados."),
        ("roundcube pre-auth", "Se explota activamente una vulnerabilidad de inyección SQL en Roundcube", "El Centro Canadiense de Ciberseguridad advirtió que la vulnerabilidad CVE-2026-48842, ya corregida, está siendo explotada. Actualiza Roundcube a una versión corregida."),
        ("cloudflare fixes flaw", "Cloudflare corrige una falla que podía exponer datos residuales entre clientes", "La falla en Cloudflare Containers podía permitir leer datos que otros contenedores habían dejado en el disco del mismo servidor. Revisa el aviso del proveedor y sus medidas aplicadas."),
        ("wso2 and adobe commerce", "CISA añade fallas explotadas de WSO2 y Adobe Commerce a su catálogo", "CISA incorporó vulnerabilidades de WSO2 y Adobe Commerce/Magento al catálogo KEV por evidencia de explotación activa. Comprueba si tus sistemas están afectados y aplica las correcciones."),
        ("unpatched oneplus", "Fallas de OnePlus podían dar permisos de administrador a aplicaciones Android", "Un investigador mostró que fallas en software de OnePlus podían permitir a una aplicación instalada obtener acceso de administrador. Comprueba las actualizaciones del fabricante."),
        ("threatsday:", "Resumen semanal: riesgos en buscadores y herramientas de programación con IA", "El resumen reúne riesgos de envenenamiento de búsquedas, exposición de repositorios y ejecución de código. Revisa permisos, fuentes y controles antes de confiar en herramientas automatizadas."),
        ("placeholder third-party", "Un dominio de ejemplo aparece en repositorios y ahora distribuye contenido malicioso", "El dominio third-party[.]com, usado como marcador de posición en documentación, fue observado mostrando señuelos maliciosos a navegadores Windows. Comprueba y sustituye referencias inseguras."),
    ]
    for needle, title, summary in translated:
        if needle in key:
            return title, summary

    # Para noticias nuevas, ofrece un encabezado y contexto defensivo en español.
    if any(word in key for word in ("malware", "stealer", "backdoor", "spyware", "trojan", "rat ")):
        category = "Nueva actividad de malware"
        summary = "La publicación describe malware o una campaña relacionada. Verifica los indicadores en la fuente original y aplica las medidas preventivas recomendadas."
    elif any(word in key for word in ("flaw", "vulnerab", "cve-", "zero-day", "0-day", "rce")):
        category = "Aviso de vulnerabilidad y seguridad"
        summary = "La publicación describe una falla de seguridad. Identifica los productos afectados y revisa si hay actualizaciones o mitigaciones disponibles."
    elif any(word in key for word in ("attack", "hacked", "compromis", "stole", "breach", "phishing")):
        category = "Alerta sobre ataques e intrusiones"
        summary = "La publicación reporta actividad de ataque o una posible intrusión. Consulta la fuente original para confirmar el alcance y las acciones recomendadas."
    else:
        category = "Actualización de ciberseguridad"
        summary = "Consulta la fuente original para conocer los detalles, los productos afectados y las medidas recomendadas."
    return category, summary


def _draw_publication_card(
    pdf: ReportPDF,
    x: float,
    y: float,
    width: float,
    item: dict[str, str],
    number: int,
) -> None:
    height = 33
    accent = (RED, BLUE, TEAL, GOLD)[(number - 1) % 4]
    pdf.set_draw_color(*BORDER)
    pdf.set_fill_color(*WHITE)
    pdf.rect(x, y, width, height, style="DF")
    pdf.set_fill_color(*accent)
    pdf.rect(x, y, 2, height, style="F")
    title, summary = _spanish_publication(item)
    _write_text(pdf, x + 6, y + 2.7, width - 12, _truncate(title, 90), 8.5, INK, True, 3.8)
    source = item.get("source", "Fuente consultada")
    published = item.get("date", "")
    _write_text(pdf, x + 6, y + 12, width - 12, f"{source}  |  {published}", 7.5, accent, True, 3.5)
    _write_text(pdf, x + 6, y + 17, width - 12, _truncate(summary, 115), 7.4, MUTED, line_height=3.4)
    if item.get("url"):
        pdf.set_xy(x + width - 30, y + 27.5)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*BLUE)
        pdf.cell(24, 3, "VER FUENTE", link=item["url"], align="R")


def _draw_page_two(pdf: ReportPDF, publications: list[dict[str, str]]) -> None:
    pdf.set_fill_color(*PALE)
    pdf.rect(0, 34, PAGE_W, PAGE_H - 34, style="F")
    _write_text(pdf, 10, 38, 175, "Selección de noticias y avisos de la semana", 12, INK, True, 6)
    _write_text(pdf, 10, 45, 270, "Cada tarjeta enlaza a su fuente original. Lee el contexto completo antes de aplicar cambios.", 8.5, MUTED, line_height=4)

    entries = publications[:MAX_PUBLICATIONS_IN_PDF]
    if not entries:
        _panel(pdf, 10, 55, 277, 35, "Fuentes consultadas", BLUE)
        _write_text(pdf, 15, 69, 265, "El informe no incluyó publicaciones detalladas. Visita el panel web para consultar las fuentes actuales.", 9, TEXT)
        return

    start_y = 55
    card_h = 33
    gap_y = 4
    col_w = 135.5
    for index, item in enumerate(entries):
        column = index // 4
        row = index % 4
        x = 10 + column * 141.5
        y = start_y + row * (card_h + gap_y)
        _draw_publication_card(pdf, x, y, col_w, item, index + 1)

    pdf.set_fill_color(*INK)
    pdf.rect(10, 203, 277, 5, style="F")
    pdf.set_xy(14, 203.5)
    pdf.set_font("Helvetica", "B", 6.5)
    pdf.set_text_color(*WHITE)
    pdf.cell(269, 4, "INFORME SEMANAL DE CIBERSEGURIDAD - RESUMEN DEFENSIVO", align="C")


def build_pdf(report_markdown: str, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    publications = _parse_publications(report_markdown)

    pdf = ReportPDF(orientation="L", format="A4")
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    pdf.set_auto_page_break(auto=False, margin=MARGIN)
    pdf.add_page()
    _draw_header(pdf, "Boletín de seguridad informática", "Ciberseguridad - radar semanal y acciones", 1)
    _draw_page_one(pdf, report_markdown, publications)

    pdf.add_page()
    _draw_header(pdf, "Fuentes y actualidad", "Noticias destacadas - seleccionadas para una lectura rápida", 2)
    _draw_page_two(pdf, publications)

    pdf.output(str(output_path))
    print("    -> Infografia PDF de dos paginas escrita correctamente.", flush=True)
    return output_path
