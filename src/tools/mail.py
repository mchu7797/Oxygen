import smtplib
from email.mime.text import MIMEText

from src.config import EMAIL_CONFIG


def send_password_reset_mail(destination_email, token):
    message = MIMEText(f"To reset your account password, take this token, {token}")
    message["Subject"] = "Password Reset"
    message["From"] = EMAIL_CONFIG["mail"]
    message["To"] = destination_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(EMAIL_CONFIG["mail"], EMAIL_CONFIG["password"])
        smtp_server.sendmail(
            EMAIL_CONFIG["mail"], destination_email, message.as_string()
        )


def send_account_id_notice_mail(destination_email, account_id):
    message = MIMEText(f"Your account's id is {account_id}.")
    message["Subject"] = "Account Notice"
    message["From"] = EMAIL_CONFIG["mail"]
    message["To"] = destination_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(EMAIL_CONFIG["mail"], EMAIL_CONFIG["password"])
        smtp_server.sendmail(
            EMAIL_CONFIG["mail"], destination_email, message.as_string()
        )


def send_nickname_change_notice_mail(destination_email, token):
    message = MIMEText(f"To change your nickname, take this token, {token}")
    message["Subject"] = "Change Nickname"
    message["From"] = EMAIL_CONFIG["mail"]
    message["To"] = destination_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(EMAIL_CONFIG["mail"], EMAIL_CONFIG["password"])
        smtp_server.sendmail(
            EMAIL_CONFIG["mail"], destination_email, message.as_string()
        )
