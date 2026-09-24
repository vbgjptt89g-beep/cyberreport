"""Recopila fuentes a diario y genera/envía un informe semanal en PDF."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

from src.fetch_sources import collect_and_store_weekly_entries, load_weekly_entries
from src.generate_pdf import build_pdf
from src.send_email import send_report_email
from src.summarize import generate_report


def main() -> None:
    load_dotenv()
    command = sys.argv[1] if len(sys.argv) > 1 else "collect"

    if command == "collect":
        collect_and_store_weekly_entries(days=7)
        return

    if command != "report":
        raise SystemExit("Uso: python main.py [collect|report]")

    entries = load_weekly_entries(days=7)
    print(f"1/4 - Preparando informe con {len(entries)} publicaciones guardadas esta semana...")
    report_markdown = generate_report(entries)

    # GitHub Actions corre en UTC; Honduras permanece en UTC-6.
    local_date = (datetime.now(timezone.utc) - timedelta(hours=6)).date()
    output_path = Path("reportes") / f"informe-ciberseguridad-{local_date:%Y-%m-%d}.pdf"
    print("2/4 - Creando el PDF...")
    build_pdf(report_markdown, output_path)
    print(f"    -> PDF creado en {output_path}")

    print("3/4 - Enviando por correo si está configurado...")
    try:
        send_report_email(output_path)
    except Exception as exc:  # El PDF y su artefacto deben conservarse aunque falle SMTP.
        print(f"[WARN] No se pudo enviar el correo; el PDF sigue disponible: {exc}")
    print("4/4 - Listo.")


if __name__ == "__main__":
    main()
