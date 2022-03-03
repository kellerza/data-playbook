"""Sending files."""
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from socket import gaierror
from typing import List, Optional, Union

from dataplaybook import task


@task
def mail(
    to_addrs: Union[List[str], str],
    from_addr: str,
    subject: str,
    files: Optional[List[str]] = None,
    priority: int = 4,
    body: Optional[str] = "",
    html: Optional[str] = "",
    server: Optional[str] = None,
    cc_addrs: Optional[List[str]] = None,
    bcc_addrs: Optional[List[str]] = None,
):
    """Send a mail."""
    cc_addrs = cc_addrs or []
    bcc_addrs = bcc_addrs or []
    if isinstance(to_addrs, str):
        to_addrs = [to_addrs]
    # Create a multipart message and set headers
    if body and html:
        message = MIMEMultipart("alternative")
    else:
        message = MIMEMultipart()
    message["From"] = from_addr
    message["To"] = "; ".join(to_addrs)
    message["Cc"] = "; ".join(cc_addrs)
    message["X-Priority"] = str(priority)
    message["Subject"] = subject

    if files:
        for file_path in list(files):
            _fp = Path(file_path)
            if not _fp.exists:
                files.pop(files.index(file_path))  # Remove if not found
                body = "Attachment not found: {file_path}\n{body}"

    # Add body to email
    if body:
        message.attach(MIMEText(body, "plain", "utf-8"))
    if html:
        message.attach(MIMEText(html, "html", "utf-8"))

    for file_path in files or []:
        _attach(message, Path(file_path))

    msg = message.as_string()

    # Log in to server using secure context and send email
    # context = ssl.create_default_context()
    try:
        with smtplib.SMTP(server, 25) as smtpserver:
            # server.login(sender_email, "")  # password)
            smtpserver.sendmail(
                from_addr=from_addr,
                to_addrs=list(set(to_addrs + cc_addrs + bcc_addrs)),
                msg=msg,
            )
    except gaierror:
        print(f"{server} not reachable")
        raise


def _attach(message, path):
    """Attach a file to message."""
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
    part.add_header("Content-Disposition", f"attachment; filename= {path.name}")

    # Add attachment to message and convert message to string
    message.attach(part)
