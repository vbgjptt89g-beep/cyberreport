"""
Envía el PDF generado como adjunto por correo electrónico usando SMTP
(compatible con Gmail usando una "contraseña de aplicación").
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_report_email(pdf_path: str | Path) -> None:
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    email_from = os.environ["EMAIL_ADDRESS"]
    email_password = os.environ["EMAIL_PASSWORD"]
    email_to = os.environ["EMAIL_TO"]  # puede ser varios separados por coma

    pdf_path = Path(pdf_path)

    msg = EmailMessage()
    msg["Subject"] = f"Informe semanal de ciberseguridad - {pdf_path.stem}"
    msg["From"] = email_from
    msg["To"] = email_to
    msg.set_content(
        "Hola,\n\n"
        "Adjunto el informe semanal de recomendaciones de ciberseguridad "
        "generado automáticamente.\n\n"
        "Saludos,\nTu asistente de ciberseguridad"
    )

    with open(pdf_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=pdf_path.name,
        )

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(email_from, email_password)
        server.send_message(msg)

    print(f"Correo enviado a {email_to} con el adjunto {pdf_path.name}")
