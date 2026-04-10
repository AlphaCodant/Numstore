"""
Envoi d'emails via SMTP (équivalent nodemailer).
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


SMTP_HOST = os.getenv("SMTP_HOST", "mail.privateemail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "admin@gestreb.net")
SMTP_PASS = os.getenv("SMTP_PASS", "")


def send_email(to: str, subject: str, body: str) -> None:
    """Envoie un email en texte brut. Ne lève pas d'exception si l'envoi échoue."""
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to, msg.as_string())
    except Exception as exc:
        # On logue l'erreur sans bloquer le flux principal
        print(f"[EMAIL] Erreur d'envoi vers {to} : {exc}")
