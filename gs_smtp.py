import smtplib
from email.message import EmailMessage


def send_key_email(
    smtp_host: str,
    smtp_port: int,
    recipient: str,
    employee_name: str,
    key: str,
    smtp_user: str = "adjumanyyann21@gmail.com",
    smtp_pass: str = "wcab xvuo eyab izwr",
):
    msg = EmailMessage()
    msg["Subject"] = "Clé confidentielle – Attribution cadeau"
    msg["From"] = smtp_user
    msg["To"] = recipient
    msg.set_content(
        f"Bonjour {employee_name},\n\n"
        f"Voici votre clé personnelle pour consulter votre attribution cadeau : {key}\n\n"
        "Cette clé est STRICTEMENT CONFIDENTIELLE : ne la partagez pas.\n"
        "Pour consulter votre attribution, lancez l'application et choisissez 'Voir mon attribution', "
        "puis entrez la clé.\n\n"
        "Merci.\n"
    )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
