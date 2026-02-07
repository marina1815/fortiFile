# emailsender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

EMAIL_SENDER = "fortifile.app@gmail.com"
EMAIL_PASSWORD = "qsvd zsrr omvy nwzt"


def send_confirmation_email(receiver_email, username):
    """
    Envoie un e-mail de confirmation après l'inscription.
    Utilise le SMTP de Gmail avec TLS.
    """
    subject = "Confirmation de création de compte"
    body = f"""
    Bonjour {username},

    🎉 Votre compte a été créé avec succès sur notre application File Integrity Monitor !

    Vous pouvez maintenant vous connecter et profiter de toutes les fonctionnalités.

    Merci de votre confiance,
    — L’équipe Sécurité 🛡️
    """

    # Création du message
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Connexion au serveur SMTP Gmail
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Sécurise la connexion
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        # Envoi du message
        server.send_message(msg)
        server.quit()

        print(" E-mail envoyé avec succès à :", receiver_email)
        return True

    except Exception as e:
        print(" Erreur d’envoi :", e)
        return False
def generate_code():
    """Génère un code de confirmation à 6 chiffres."""
    return str(random.randint(100000, 999999))

def send_code_confirmation_email(to_email, username, code):
    """Envoie un e-mail contenant le code de confirmation."""
    subject = "Code de confirmation - File Integrity Monitor"
    body = f"""
    Bonjour {username},

    Voici votre code de confirmation : {code}

    Entrez ce code dans l'application pour finaliser votre inscription.

    -- L'équipe File Integrity Monitor
    """
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print("Erreur d’envoi :", e)
        return False


def send_custom_email(username, user_email, message):
    """Envoie un e-mail contenant le code de confirmation."""
    subject = f"[Help Request] Message from {username}"
    body = f"""
        You received a new help request from {username} ({user_email}):

        -------------------------------
        {message}
        -------------------------------
        """
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = "fortifile.app@gmail.com"
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print("Erreur d’envoi :", e)
        return False