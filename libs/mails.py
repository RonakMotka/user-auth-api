import smtplib
import traceback

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import HTTPException, status

from config import config


def send_mail(email: str, subject: str, body: str):
    try:
        password = config["mail_pass"]
        host = config["mail_host"]
        port = config["port"]
        sender = config["from_email"]
        recipient = email
        subject = subject
        body_html = body

        message = MIMEMultipart("alternative")
        message['Subject'] = subject
        message['From'] = f"{subject} <{sender}>"
        message["To"] = recipient

        html_part = MIMEText(body_html, 'html')
        message.attach(html_part)
        smtp = smtplib.SMTP(host, port)
        smtp.ehlo()
        smtp.starttls()
        smtp.login(sender, password)
        smtp.sendmail(sender, recipient, message.as_string())
        smtp.quit()
        return
    
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    