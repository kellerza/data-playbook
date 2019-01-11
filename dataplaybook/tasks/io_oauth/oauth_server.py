"""Requests-OAuthlib sample for Microsoft Graph.

Uses Authorization code grant

https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#web-application-flow

 """

import logging
import os
import signal

import bottle

_LOGGER = logging.getLogger(__name__)
SESSION = None
SERVER = None

# Enable non-HTTPS redirect URI for development/testing.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# Allow token scope to not match requested scope. (Other auth libraries allow
# this, but Requests-OAuthlib raises exception on scope mismatch by default.)
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'

bottle.TEMPLATE_PATH = ['./static/templates']


def start(session):
    """Start the local websever for auth callbacks."""

    # Allow Ctrl-C break
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    global SERVER, SESSION
    SESSION = session

    app = bottle.app()
    try:
        SERVER = MyWSGIRefServer(host=session.host, port=session.port)
        app.run(server=SERVER)
    except Exception as exc:  # pylint: disable=broad-except
        _LOGGER.error(exc)


@bottle.route('/')
def login():
    """Prompt user to authenticate."""
    return bottle.redirect(SESSION.authorization_url)


@bottle.route('/login/authorized')
def authorized():
    """Handler for the application's Redirect Uri."""
    # pylint: disable=E1101
    if bottle.request.query.state != SESSION.session.auth_state:
        raise Exception('state returned to redirect URL does not match!')
    SESSION.fetch_token(bottle.request.url)
    return bottle.redirect('/ok')


@bottle.route('/ok')
def graphcall():
    """Confirm user authentication by calling Graph and displaying data."""
    res = SESSION.get('https://graph.microsoft.com/v1.0/me')

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
