"""Simple bottle server to receive authorization callback."""
import logging
import os
import signal

import bottle

_LOGGER = logging.getLogger(__name__)
CON = None
SERVER = None

# Enable non-HTTPS redirect URI for development/testing.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def start(connection):
    """Start the local websever for auth callbacks."""
    # Allow Ctrl-C break
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    global SERVER, CON
    CON = connection

    app = bottle.app()
    try:
        SERVER = MyWSGIRefServer(host='localhost', port=5000)
        app.run(server=SERVER)
    except Exception as exc:  # pylint: disable=broad-except
        _LOGGER.error(exc)


@bottle.route('/')
def login():
    """Prompt user to authenticate."""
    redirect_uri = "http://{}:{}/login/authorized".format(
        SERVER.host, SERVER.port)
    return bottle.redirect(
        CON.get_authorization_url(redirect_uri=redirect_uri))


@bottle.route('/login/authorized')
def callback():
    """Handler for the application's Redirect Uri.

    Request the token, some data to test the token and shutdown the server."""
    CON.request_token(bottle.request.url)

    res = CON.get('https://graph.microsoft.com/v1.0/me').json()

    return SERVER.shutdown() + str(res)


class MyWSGIRefServer(bottle.WSGIRefServer):
    """WSGI server with shutdown."""
    server = None

    def run(self, handler):  # pylint: disable=W0221
        """Run the server."""
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                """Quiet handler."""
                def log_request(self, *_, **__):  # pylint: disable=W0221
                    pass
            self.options['handler_class'] = QuietHandler
        self.server = make_server(
            self.host, self.port, handler, **self.options)
        self.server.serve_forever(poll_interval=0.5)

    def shutdown(self):
        """Shutdown the server in another thread."""
        import threading
        threading.Thread(target=self.server.shutdown).start()
        return "BYE"
