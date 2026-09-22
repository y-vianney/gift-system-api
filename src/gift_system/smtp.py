from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .config import APP_URL, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER


def send_key_email(
    email: str,
    name: str,
    key: str,
    smtp_host: str | None = None,
    smtp_port: int | None = None,
    smtp_user: str | None = None,
    smtp_pass: str | None = None,
) -> None:
    host = smtp_host or SMTP_HOST
    port = smtp_port or SMTP_PORT
    sender = smtp_user or SMTP_USER
    password = smtp_pass or SMTP_PASSWORD

    if not sender or not password:
        raise RuntimeError("SMTP credentials are not configured. Set SMTP_USER and SMTP_PASSWORD.")

    html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <p>Bonjour <strong>{name}</strong>,</p>
            <p>La répartition des cadeaux pour notre Secret Santa a été effectuée !</p>
            <p>
                Votre clé personnelle confidentielle :
                <span style="font-size: 1.2em; color: #d9534f; font-weight: bold;">{key}</span>
            </p>
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #ddd;">
                <strong>COMMENT ÇA MARCHE ?</strong><br>
                1. Cliquez sur ce lien : <a href="{APP_URL}">{APP_URL}</a><br>
                2. Entrez votre clé ci-dessus pour découvrir qui vous avez pioché.<br>
                3. Gardez ce nom <strong>STRICTEMENT CONFIDENTIEL</strong>.
            </div>
            <p>Merci et bonnes fêtes !</p>
        </body>
        </html>
    """

    msg = EmailMessage()
    msg["Subject"] = "🎁 Secret Santa : Votre clé d'attribution (Confidentiel)"
    msg["From"] = sender
    msg["To"] = email

    msg.set_content(
        f"Bonjour, Bonsoir {name} ,\n\n"
        "La répartition des cadeaux pour notre Secret Santa a été effectuée !\n\n"
        f"Votre clé personnelle confidentielle : **{key}**\n\n"
        "--- COMMENT ÇA MARCHE ? ---\n"
        f"1. Cliquez sur ce lien : {APP_URL}\n"
        "2. Entrez votre clé ci-dessus pour découvrir qui vous avez pioché.\n"
        "3. Gardez ce nom STRICTEMENT CONFIDENTIEL.\n\n"
        "Merci et bonnes fêtes !"
    )
    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
