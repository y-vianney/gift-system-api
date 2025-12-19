import smtplib
from email.message import EmailMessage


def send_key_email(
    smtp_host: str,
    smtp_port: int,
    email: str,
    name: str,
    key: str,
    smtp_user: str = "adjumanyyann21@gmail.com",
    smtp_pass: str = "wcab xvuo eyab izwr",
):
    html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <p>Bonjour <strong>{name}</strong>,</p>

            <p>La répartition des cadeaux pour notre Secret Santa a été effectuée !</p>

            <p>
                Votre clé personnelle confidentielle :
                <span style="font-size: 1.2em; color: #d9534f; font-weight: bold;">
                    {key}
                </span>
            </p>

            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #ddd;">
                <strong>COMMENT ÇA MARCHE ?</strong><br>
                1. Cliquez sur ce lien : <a href="https://end-year-cdn.vercel.app">https://end-year-cdn.vercel.app</a><br>
                2. Entrez votre clé ci-dessus pour découvrir qui vous avez pioché.<br>
                3. Gardez ce nom <strong>STRICTEMENT CONFIDENTIEL</strong>.
            </div>

            <p><strong>INFOS PRATIQUES</strong><br>
            📅 Date du repas : 29 Décembre à partir de 13h.<br>
            💰 Budget suggéré : 5000 FCFA, pour côtisations.</p>

            <p>Merci et bonnes fêtes !</p>

            <hr style="border: 0; border-top: 1px solid #eee; margin-top: 20px;">
            <p style="color: #888888; font-style: italic; font-size: 0.85em;">
                Ce message est généré automatiquement, merci de ne pas y répondre.
            </p>
        </body>
        </html>
    """

    msg = EmailMessage()
    msg["Subject"] = "🎁 Secret Santa : Votre clé d'attribution (Confidentiel)"
    msg["From"] = smtp_user
    msg["To"] = email

    msg.set_content(
        f"Bonjour, Bonsoir {name} ,\n\n"
        "La répartition des cadeaux pour notre Secret Santa a été effectuée !\n\n"
        f"Votre clé personnelle confidentielle : **{key}**\n\n"
        "--- COMMENT ÇA MARCHE ? ---\n"
        "1. Cliquez sur ce lien : https://end-year-cdn.vercel.app\n"
        "2. Entrez votre clé ci-dessus pour découvrir qui vous avez pioché.\n"
        "3. Gardez ce nom STRICTEMENT CONFIDENTIEL.\n\n"
        "--- INFOS PRATIQUES ---\n"
        "📅 Date du repas : 29 Décembre à partir de 13h (au retour des congés).\n"
        "💰 Budget suggéré : 5000 FCFA, pour côtisations.\n\n"
        "Merci et bonnes fêtes !"
    )
    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
