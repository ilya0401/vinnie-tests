import os
import requests

response = requests.post(
    'https://api.resend.com/emails',
    headers={'Authorization': f'Bearer {os.environ["RESEND_API_KEY"]}'},
    json={
        'from': 'Jenkins <onboarding@resend.dev>',
        'to': [os.environ['EMAIL_TO']],
        'subject': os.environ['EMAIL_SUBJECT'],
        'text': os.environ['EMAIL_BODY'],
    },
)

if response.ok:
    print(f"Email sent, status: {response.status_code}")
else:
    print(f"Resend error {response.status_code}: {response.text}")
    response.raise_for_status()
