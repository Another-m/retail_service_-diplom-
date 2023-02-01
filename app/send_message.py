from django.core.mail import EmailMultiAlternatives

from retail_service import settings


def send_mail(title, message, to):
    msg = EmailMultiAlternatives(
        # title:
        title,
        # message:
        message,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        to
    )
    print(msg.__dict__)
    msg.send()