from django.core.mail import send_mail, EmailMessage


def transfer_upload_email_blaster(email_address, action, message):
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

    send_mail(
        title,
        message,
        'noreply@presqt.crc.nd.edu',
        [email_address],
        fail_silently=True)


def download_email_blaster(email_address, file_path, message):
    """
    Function to send emails when a download has finished running on the server.

    Parameters
    ----------
    email_address : str
        The user's email address
    file_path : bytes
        The path to the zip file of downloaded items
    message : str
        The message to put in the body of the email
    """
    # Build the message
    message = EmailMessage(
        'PresQT Download Complete',
        message,
        'noreply@presqt.crc.nd.edu',
        [email_address]
    )
    message.attach_file(file_path)
    message.send()
