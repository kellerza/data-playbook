"""Sending files."""

import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from socket import gaierror

from dataplaybook import task


@task
def mail(  # noqa: PLR0913
    *,
    to_addrs: list[str] | str,
    from_addr: str,
    subject: str,
    server: str,
    files: list[Path | tuple[Path, str]] | None = None,
    priority: int = 4,
    body: str | None = "",
    html: str | None = "",
    cc_addrs: list[str] | None = None,
    bcc_addrs: list[str] | None = None,
) -> None:
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
        for fn in list(files):
            path, name = fn if isinstance(fn, tuple) else (fn, fn.name)
            if not path.exists():
                files.remove(fn)
                body = f"Attachment not found: {name} [{path}]\n{body}"

    # Add body to email
    if body:
        message.attach(MIMEText(body, "plain", "utf-8"))
    if html:
        message.attach(MIMEText(html, "html", "utf-8"))

    for fn in files or []:
        fpath, fname = fn if isinstance(fn, tuple) else (fn, fn.name)
        if att := attachment(fpath, fname):
            message.attach(att)

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


def attachment(path: Path, name: str) -> MIMEBase | None:
    """Attach a file to message."""
    text = path.read_bytes()
    if text is None:
        return None
    # Add file as application/octet-stream
    # Email client can usually download this automatically as attachment
    part = MIMEBase("application", "octet-stream")
    part.set_payload(text)
    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)
    # Add header as key/value pair to attachment part
    part.add_header("Content-Disposition", f"attachment; filename={name}")
    return part
