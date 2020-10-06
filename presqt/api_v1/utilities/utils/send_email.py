from django.core.mail import send_mail, EmailMessage


def email_blaster(email_address, title, message):
    """
    Function to send emails when a subprocess has finished running on the server.

    Parameters
    ----------
    email_address : str
        The user's email address
    title : str
        The email subject line
    message : str
        The message to put in the body of the email
    """
    send_mail(
        title,
        message,
        'noreply@presqt.crc.nd.edu',
        [email_address],
        fail_silently=True)
