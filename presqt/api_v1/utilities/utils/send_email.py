from django.core.mail import send_mail, EmailMessage


def email_blaster(email_address, action, message):
    """
    Function to send emails when a subprocess has finished running on the server.

    Parameters
    ----------
    email_address : str
        The user's email address
    action : str
        The action taking place
    message : str
        The message to put in the body of the email
    """
    if action == 'resource_upload':
        title = "PresQT Upload Complete"
    elif action == 'resource_transfer_in':
        title = "PresQT Transfer Complete"
    elif action == 'resource_download':
        title = "PresQT Download Complete"

    send_mail(
        title,
        message,
        'noreply@presqt.crc.nd.edu',
        [email_address],
        fail_silently=True)
