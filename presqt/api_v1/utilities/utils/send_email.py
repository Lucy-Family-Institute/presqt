from django.core.mail import send_mail, EmailMessage


def transfer_upload_email_blaster(email_address, action):
    """
    Function to send emails when a subprocess has finished running on the server.

    Parameters
    ----------
    email_address : str
        The user's email address
    action : str
        The action taking place
    """
    real_action = None
    if action == 'resource_upload':
        real_action = "upload"
    elif action == 'resource_transfer_in':
        real_action = 'transfer'

    send_mail(
        'PresQT Action Complete',
        'The {} you started on PresQT has finished.'.format(real_action),
        'noreply@presqt.crc.nd.edu',
        [email_address],
        fail_silently=True)


def download_email_blaster(email_address, file_path):
    """
    Function to send emails when a download has finished running on the server.

    Parameters
    ----------
    email_address : str
        The user's email address
    file_path : bytes
        The path to the zip file of downloaded items
    """
    # Build the message
    message = EmailMessage(
        'PresQT Action Complete',
        'The download you started on PresQT has finished. It has been attached to this email.',
        'noreply@presqt.crc.nd.edu',
        [email_address]
    )
    message.attach_file(file_path)
    message.send()
