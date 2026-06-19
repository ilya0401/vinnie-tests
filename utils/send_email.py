import os
import urllib.request
import urllib.error
import json

payload = json.dumps({
    'from': 'Jenkins <onboarding@resend.dev>',
    'to': [os.environ['EMAIL_TO']],
    'subject': os.environ['EMAIL_SUBJECT'],
    'text': os.environ['EMAIL_BODY'],
}).encode('utf-8')

req = urllib.request.Request(
    'https://api.resend.com/emails',
    data=payload,
    headers={
        'Authorization': f'Bearer {os.environ["RESEND_API_KEY"]}',
        'Content-Type': 'application/json',
    },
    method='POST',
)

with urllib.request.urlopen(req) as resp:
    print(f"Email sent, status: {resp.status}")
