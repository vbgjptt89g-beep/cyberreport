"""
Punto de entrada: obtiene fuentes -> genera informe con IA -> crea PDF -> envía por correo.
Ejecutado semanalmente por GitHub Actions (ver .github/workflows/weekly-report.yml).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from src.fetch_sources import fetch_weekly_entries
from src.generate_pdf import build_pdf
from src.send_email import send_report_email
from src.summarize import generate_report


def main() -> None:
    load_dotenv()  # útil para pruebas locales con un archivo .env

    print("1/4 - Recopilando fuentes de la semana...")
    entries = fetch_weekly_entries(days=7)
    print(f"    -> {len(entries)} publicaciones encontradas")

    print("2/4 - Generando el informe con IA...")
    report_markdown = generate_report(entries)

    print("3/4 - Creando el PDF...")
    output_path = Path("reportes") / f"informe-ciberseguridad-{date.today():%Y-%m-%d}.pdf"
    build_pdf(report_markdown, output_path)
    print(f"    -> PDF creado en {output_path}")

    print("4/4 - Enviando por correo...")
    send_report_email(output_path)

    print("Listo.")


if __name__ == "__main__":
    main()
