import smtplib
import time
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.core.mail import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ElasticEmail
from ElasticEmail.api import emails_api
from ElasticEmail.model.email_content import EmailContent
from ElasticEmail.model.body_part import BodyPart
from ElasticEmail.model.body_content_type import BodyContentType
from ElasticEmail.model.transactional_recipient import TransactionalRecipient
from ElasticEmail.model.email_transactional_message_data import EmailTransactionalMessageData
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email import encoders
from django.shortcuts import get_object_or_404
from authentication.models import CustomUser
from .models import Document
from django.template.loader import render_to_string
from django.shortcuts import HttpResponse
from fileapp.settings import EMAIL_HOST_USER
from celery import shared_task
from django.conf import settings
import requests
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


@shared_task
def share_file_task(sender_id, receiver_email):
    try:
        sender = CustomUser.objects.get(pk=sender_id)
        subject = 'A file has been shared with you by {}'.format(sender.company_name)
        with open('templates/email.html', 'r') as file:
            html_content = file.read()
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = receiver_email
        msg['Subject'] = subject

        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()  # Upgrade the connection to a secure TLS connection
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)  # Login to the SMTP server
            server.connect(settings.EMAIL_HOST, settings.EMAIL_PORT)
            server.sendmail(settings.EMAIL_HOST_USER, receiver_email, msg.as_string())  # Send the email

        print("Email sent successfully!")
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Failed to send email. Error: {e}")
        # Raise the exception so that Celery knows the task has failed
        raise Exception(f"Failed to send email. Error: {e}")


@shared_task
def file_share(sender_id, receiver_email):
    sender = CustomUser.objects.get(pk=sender_id)
    subject = 'A file has been shared with you by {}'.format(sender.company_name)
    api_key = settings.ELASTIC_API_KEY
    from_address = 'collaboration@fusionscl.com'  # Replace with your sender email address
    with open('templates/email.html', 'r') as file:
        html_content = file.read()

    url = 'https://api.elasticemail.com/v2/email/send'

    payload = {
        'apikey': api_key,
        'from': from_address,
        'to': receiver_email,
        'subject': subject,
        'bodyHtml': html_content,
        'isTransactional': True  # Set this to True for transactional emails
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Raise exception for HTTP errors

        try:
            # Attempt to parse the response content as JSON
            json_response = response.json()
            status_code = response.status_code
            status_of_email = 'Email sent successfully' if json_response.get('success',
                                                                             False) else 'Failed to send email'
            email_data = json_response.get('data', {}).get('messageid', '')
        except ValueError:
            # If response content is not valid JSON, use raw content as email_data
            status_code = response.status_code
            status_of_email = 'Failed to parse JSON response'
            email_data = response.text

        return {
            'status_code': status_code,
            'status_of_email': status_of_email,
            'email_data': email_data
        }
    except requests.exceptions.RequestException as e:
        print(f'Failed to send email: {e}')
        return {
            'status_code': 500,
            'status_of_email': 'Failed to send email',
            'email_data': str(e)
        }


@shared_task
def new_share(sender_id, receiver_email):
    sender = CustomUser.objects.get(pk=sender_id)
    subject = 'A file has been shared with you by {}'.format(sender.company_name)
    api_key = settings.ELASTIC_API_KEY
    from_address = 'collaboration@fusionscl.com'  # Replace with your sender email address
    try:
        with open('templates/email.html', 'r') as file:
            html_content = file.read()
    except Exception as e:
        print(f"Error reading email template file: {e}")
    html_content1 = f"""
            <html>
            <body>
                <p>Hello ,</p>
                <p>You have been shared a file via File Sharing App. Click the link below to download:</p>
                <a href="#">Download File</a>
            </body>
            </html>
        """
    # Defining the host is optional and defaults to https://api.elasticemail.com/v4
    configuration = ElasticEmail.Configuration()

    # Configure API key authorization: apikey
    configuration.api_key['apikey'] = settings.ELASTIC_API_KEY

    """
    Send transactional emails
    Example api call that sends transactional email.
    Limit of 50 maximum recipients.
    """
    with ElasticEmail.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = emails_api.EmailsApi(api_client)

        email_transactional_message_data = EmailTransactionalMessageData(
            recipients=TransactionalRecipient(
                to=[
                    receiver_email,
                ],
            ),
            content=EmailContent(
                body=[
                    BodyPart(
                        content_type=BodyContentType("HTML"),
                        content="<strong>{}<strong>".format(html_content1),
                        charset="utf-8",
                    ),
                    BodyPart(
                        content_type=BodyContentType("PlainText"),
                        content=html_content1,
                        charset="utf-8",
                    ),
                ],
                _from=settings.EMAIL_HOST_USER,
                reply_to=settings.EMAIL_HOST_USER,
                subject=subject,
            ),
        )  # EmailTransactionalMessageData | Email data

        try:
            # Send Transactional Email
            api_response = api_instance.emails_transactional_post(email_transactional_message_data)
            print(api_response)
        except ElasticEmail.ApiException as e:
            print("Exception when calling EmailsApi->emails_transactional_post: %s\n" % e)


@shared_task
def share(pk, sender_id, receiver_email):
    sender = CustomUser.objects.get(pk=sender_id)
    subject = 'A file has been shared with you by {}'.format(sender.company_name)
    #   api_key = settings.ELASTIC_API_KEY
    #   from_address = 'collaboration@fusionscl.com'
    template = "email.html"
    doc = Document.objects.get(pk=pk)
    download_link = doc.file.url
    message_context = {
        "download_link": download_link,
    }
    message = render_to_string(template, message_context)

    msg = EmailMessage(subject=subject, body=message, from_email=settings.EMAIL_HOST_USER, to=[receiver_email])
    msg.send()


@shared_task
def share_brevo(pk, sender_id, receiver_email):
    sender = CustomUser.objects.get(pk=sender_id)
    subject = 'A file has been shared with you by {}'.format(sender.company_name)
    BREVO_API_KEY = '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'
    try:
        with open('templates/email.html', 'r') as file:
            html_content = file.read()
    except Exception as e:
        print('File not read because of {}'.format(e))
    doc = Document.objects.get(pk=pk)
    url = "https://api.brevo.com/v1/email/send"
    payload = {
        "sender": {
            "name": "Test",
            "email": 'tpsolesi@gmail.com',
        },
        "to": [
            {
                "email": receiver_email,
            }
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        'api-key': BREVO_API_KEY
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        print("Email sent successfully!")
    else:
        print(f"Failed to send email. Status code: {response.status_code}. Error is caused by {response.content}")

@shared_task
def share_brevo2(pk, sender_id, receiver_email):
    sender = CustomUser.objects.get(pk=sender_id)
    subject = 'A file has been shared with you by {}'.format(sender.company_name)
    BREVO_API_KEY = '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'
    try:
        with open('templates/email.html', 'r') as file:
            html_content = file.read()
    except Exception as e:
        print('File not read because of {}'.format(e))
    doc = Document.objects.get(pk=pk)
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    html_content = html_content
    email_sender = [{"name": sender.first_name, "email": 'tpsolesi@gmail.com'}]
    to = [{"email": receiver_email, "name": receiver_email}]
    reply_to = {"email": 'tpsolesi@gmail.com', "name": "John Doe"}
    headers = {"fscl": "678543ju89"}
    params = {"parameter": "test_value", "subject": subject}
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, reply_to=reply_to, headers=headers,
                                                   html_content=html_content, sender=email_sender, subject=subject)

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(api_response)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
