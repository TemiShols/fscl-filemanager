from django.core.mail import EmailMultiAlternatives
from authentication.models import CustomUser
from file.models import Document
from celery import shared_task
import requests
import json


#   celery -A fileapp worker --pool=solo -l info


@shared_task
def send_simple_download_message(doc_id, context_json):
    doc = Document.objects.get(pk=doc_id)
    context_data = json.loads(context_json)
    subject = 'File, {}, downloaded'.format(doc.name)
    with open('templates/download_file.txt', 'r') as file:
        content = file.read()
    content = content.replace('{{ doc.name }}', context_data['doc_name'])
    content = content.replace('{{ doc.user.get_full_name }}', context_data['sender_name'])
    return requests.post(
        "https://api.mailgun.net/v3/mg.neo-urban.ng/messages",
        auth=("api", "4b886c6df7ccbe4dd11af9d995c56116-2b755df8-4300fbed"),
        data={"from": "Testing <postmaster@mg.neo-urban.ng>",
              "to": [doc.user.email],
              "subject": subject,
              "text": content})


@shared_task
def send_simple_share_message(sender_id, receiver_email, context_json):
    sender = CustomUser.objects.get(pk=sender_id)
    context_data = json.loads(context_json)
    subject = 'File Shared with You by {}'.format(sender.company_name)
    with open('templates/share_email.txt', 'r') as file:
        content = file.read()
    content = content.replace('{{ doc.name }}', context_data['doc_name'])
    content = content.replace('{{ doc.file.url }}', context_data['file_url'])
    content = content.replace('{{ doc.user.get_full_name }}', context_data['sender_name'])
    content = content.replace('{{ doc.user.company_name }}', context_data['company_name'])
    return requests.post(
        "https://api.mailgun.net/v3/mg.neo-urban.ng/messages",
        auth=("api", "4b886c6df7ccbe4dd11af9d995c56116-2b755df8-4300fbed"),
        data={"from": "FSCL <postmaster@mg.neo-urban.ng>",
              "to": [receiver_email],
              "subject": subject,
              "text": content})
