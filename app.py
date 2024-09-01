import email
import imaplib
import openai
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configurations
email_user = os.getenv("EMAIL_USER")
email_pass = os.getenv("EMAIL_PASS")
smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
openai_api_key = os.getenv("OPENAI_API_KEY")

openai.api_key = openai_api_key

def fetch_unread_emails():
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(email_user, email_pass)
    mail.select('inbox')
    status, messages = mail.search(None, '(UNSEEN)')
    email_ids = messages[0].split()
    emails = []
    for e_id in email_ids:
        _, msg_data = mail.fetch(e_id, '(RFC822)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                emails.append(msg)
    return emails

def check_if_fraudulent(email_content):
    prompt = f"Le mail suivant est-il frauduleux ? \n\n{email_content}"
    response = openai.Completion.create(
        engine="gpt-4",
        prompt=prompt,
        max_tokens=100
    )
    return response.choices[0].text.strip()

def send_email_response(recipient_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = email_user
    msg['To'] = recipient_email

    with smtplib.SMTP_SSL(smtp_server) as server:
        server.login(email_user, email_pass)
        server.sendmail(email_user, recipient_email, msg.as_string())

def process_emails():
    emails = fetch_unread_emails()
    for msg in emails:
        email_content = msg.get_payload(decode=True).decode()
        sender_email = msg['From']
        subject = msg['Subject']
        
        # Vérifier si le mail est frauduleux
        result = check_if_fraudulent(email_content)
        
        # Envoyer une réponse au destinataire
        send_email_response(sender_email, subject, result)

# Exécuter le processus de manière récurrente
process_emails()
