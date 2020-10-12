import html2text

from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.core.mail import send_mail


def email_blaster(email_address, title, context, template_path):
    """
    Function to send emails when a subprocess has finished running on the server.

    Parameters
    ----------
    email_address : str
        The user's email address
    title : str
        The email subject line
    context : dict
        Info to inject into templates
    template_path : str
        The path to the email template
    """
    template = get_template(template_path)
    html_code = template.render(context)

    send_mail(
        subject=title,
        message=html2text.html2text(html_code),
        html_message=html_code,
        from_email="PresQT <noreply@presqt.crc.nd.edu>",
        recipient_list=[email_address],
        fail_silently=True)
