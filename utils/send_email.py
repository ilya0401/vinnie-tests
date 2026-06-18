import smtplib
import os
from email.mime.text import MIMEText

msg = MIMEText(os.environ['EMAIL_BODY'], 'plain', 'utf-8')
msg['Subject'] = os.environ['EMAIL_SUBJECT']
msg['From'] = os.environ['GMAIL_USER']
msg['To'] = os.environ['EMAIL_TO']

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(os.environ['GMAIL_USER'], os.environ['GMAIL_PASS'])
    smtp.send_message(msg)

print(f"Email sent to {os.environ['EMAIL_TO']}")
