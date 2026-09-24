"""Envía opcionalmente el PDF por SMTP; el artefacto de Actions queda disponible sin email."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_report_email(pdf_path: str | Path) -> bool:
    email_from = os.environ.get("EMAIL_ADDRESS")
    email_password = os.environ.get("EMAIL_PASSWORD")
    email_to = os.environ.get("EMAIL_TO")
    if not all((email_from, email_password, email_to)):
        print("No se configuró correo; descarga el PDF desde el artefacto de GitHub Actions.")
        return False

    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    pdf_path = Path(pdf_path)
    msg = EmailMessage()
    msg["Subject"] = f"Informe semanal de ciberseguridad - {pdf_path.stem}"
    msg["From"] = email_from
    msg["To"] = email_to
    msg.set_content("Hola,\n\nAdjunto el informe semanal de ciberseguridad.\n")
    msg.add_attachment(
        pdf_path.read_bytes(), maintype="application", subtype="pdf", filename=pdf_path.name,
    )
    with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20) as server:
        server.login(email_from, email_password)
        server.send_message(msg)
    print(f"Correo enviado a {email_to} con el adjunto {pdf_path.name}")
    return True
