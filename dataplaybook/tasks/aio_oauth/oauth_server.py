"""Simple bottle server to receive authorization callback."""
import logging
import os
import signal
from threading import Thread
from typing import Any, NoReturn
from wsgiref.simple_server import WSGIRequestHandler, make_server

import bottle

_LOGGER = logging.getLogger(__name__)
CON = None
SERVER = None

# Enable non-HTTPS redirect URI for development/testing.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


def start(connection) -> None:
    """Start the local websever for auth callbacks."""
    # Allow Ctrl-C break
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    global SERVER, CON
    CON = connection

    app = bottle.app()
    try:
        SERVER = MyWSGIRefServer(host="localhost", port=5000)
        app.run(server=SERVER)
    except Exception as exc:  # pylint: disable=broad-except
        _LOGGER.error(exc)


@bottle.route("/")
def login() -> NoReturn:
    """Prompt user to authenticate."""
    redirect_uri = f"http://{SERVER.host}:{SERVER.port}/login/authorized"

    (auth_url, _) = CON.get_authorization_url(redirect_uri=redirect_uri)

    _LOGGER.debug("URL: %s, auth_url %s", redirect_uri, auth_url)

    return bottle.redirect(auth_url)


@bottle.route("/login/authorized")
def callback() -> str:
    """Handle the application's Redirect Uri.

    Request the token, some data to test the token and shutdown the server.
    """
    CON.request_token(bottle.request.url)

    res = CON.get("https://graph.microsoft.com/v1.0/me").json()

    return SERVER.shutdown() + str(res)


class MyWSGIRefServer(bottle.WSGIRefServer):
    """WSGI server with shutdown."""

    server = None

    def run(self, app: Any) -> None:
        """Run the server."""
        if self.quiet:

            class QuietHandler(WSGIRequestHandler):
                """Quiet handler."""

                def log_request(self, *_, **__):  # pylint: disable=signature-differs
                    pass

            self.options["handler_class"] = QuietHandler
        self.server = make_server(self.host, self.port, app, **self.options)
        self.server.serve_forever(poll_interval=0.5)

    def shutdown(self) -> str:
        """Shutdown the server in another thread."""
        Thread(target=self.server.shutdown).start()
        return "BYE"
