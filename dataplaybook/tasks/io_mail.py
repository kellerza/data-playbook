"""Sending files."""
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import voluptuous as vol
from dataplaybook import config_validation as cv


@cv.task_schema({
    vol.Required('from_addr'): str,
    vol.Required('to_addrs'): vol.All(cv.ensure_list, [str]),
    vol.Required('files'): vol.All(cv.ensure_list, [str]),
    vol.Required('body'): str,
    vol.Required('subject'): str,
    vol.Optional('priority'): str,
    vol.Optional('server'): str,
}, kwargs=True)
def task_mail(_, to_addrs, from_addr, files, body, subject,
              priority=4, server=None):
    """Send a mail."""
    # Create a multipart message and set headers
    message = MIMEMultipart()
    message['From'] = from_addr
    message['To'] = '; '.join(to_addrs)
    message['X-Priority'] = str(priority)
    message['Subject'] = subject

    for file_path in list(files):
        _fp = Path(file_path)
        if not _fp.exists:
            files.pop(files.index(file_path))  # Remove if not found
            body = "Attachment not found: {file_path}\n{body}"

    # Add body to email
    message.attach(MIMEText(body, 'plain'))

    for file_path in files:
        attach(message, Path(file_path))

    msg = message.as_string()

    # Log in to server using secure context and send email
    # context = ssl.create_default_context()
    with smtplib.SMTP(server, 25) as smtpserver:
        # server.login(sender_email, "")  # password)
        smtpserver.sendmail(from_addr=from_addr, to_addrs=to_addrs, msg=msg)


def attach(message, path):
    """Attache a file to message."""
    assert isinstance(path, Path)

    text = path.read_bytes()
    if text is None:
        return

    # Open file in binary mode
    # with path.open('rb') as fpt:
    # Add file as application/octet-stream
    # Email client can usually download this automatically as attachment
    part = MIMEBase("application", "octet-stream")
    part.set_payload(text)

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {path.name}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
