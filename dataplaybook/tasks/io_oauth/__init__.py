"""Requests-OAuthlib sample for Microsoft Graph """
import logging
import os

import attr
import bottle
import requests_oauthlib
import voluptuous as vol
import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)
CONFIG = None
SERVER = None


@attr.s(slots=True)
class Config(object):
    """Oauth config."""
    client_id = attr.ib()
    client_secret = attr.ib()
    session = attr.ib(init=False)
    scopes = attr.ib(default=['User.read'])
    port = attr.ib(default=5000)
    host = attr.ib(default='localhost')
    authority_url = attr.ib(
        default="https://login.microsoftonline.com/organizations")
    auth_endpoint = attr.ib(default="/oauth2/v2.0/authorize")
    token_endpoint = attr.ib(default="/oauth2/v2.0/token")

    def init_session(self):
        """Initialize the requests session."""
        redirect_url = "http://{}:{}/login/authorized".format(
            self.host, self.port)
        self.session = requests_oauthlib.OAuth2Session(
            self.client_id,
            scope=self.scopes,
            redirect_uri=redirect_url
        )

    def authorization_url(self):
        """Return the authorization URL / redirect target."""
        auth_base = self.authority_url + self.auth_endpoint
        a_url, state = self.session.authorization_url(auth_base)
        self.session.auth_state = state
        return a_url

    def fetch_token(self, auth_response):
        """Fetch the Token."""
        self.session.fetch_token(
            self.authority_url + self.token_endpoint,
            client_secret=self.client_secret,
            authorization_response=auth_response
        )

    def get_schema(self):
        """Generate the olutios schema with all attrs defaults."""
        return {
            vol.Required('client_id'): str,
            vol.Required('client_secret'): str,
            vol.Required('scopes', default=self.scopes): vol.All(
                cv.ensure_list, [str]),
            vol.Optional('authority_url', default=self.authority_url): str,
            vol.Optional('auth_endpoint', default=self.auth_endpoint): str,
            vol.Optional('host', default=self.host): str,
            vol.Optional('port', default=self.port): int
        }


# Enable non-HTTPS redirect URI for development/testing.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# Allow token scope to not match requested scope. (Other auth libraries allow
# this, but Requests-OAuthlib raises exception on scope mismatch by default.)
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'

bottle.TEMPLATE_PATH = ['./static/templates']

# @bottle.route('/')
# @bottle.view('homepage.html')
# def homepage():
#     """Render the home page."""
#     return {'sample': 'Requests-OAuthlib'}


@bottle.route('/')
def login():
    """Prompt user to authenticate."""
    return SERVER.shutdown()
    # return bottle.redirect(CONFIG.authorization_url())


@bottle.route('/login/authorized')
def authorized():
    """Handler for the application's Redirect Uri."""
    if bottle.request.query.state != CONFIG.session.auth_state:
        raise Exception('state returned to redirect URL does not match!')
    CONFIG.fetch_token(bottle.request.url)
    return SERVER.shutdown()
    # return bottle.redirect('/graphcall')


# @bottle.route('/graphcall')
# @bottle.view('graphcall.html')
# def graphcall():
#     """Confirm user authentication by calling Graph and displaying data."""
#     endpoint = config.RESOURCE + config.API_VERSION + '/me'
#     headers = {'SdkVersion': 'sample-python-requests-0.1.0',
#                'x-client-SKU': 'sample-python-requests',
#                'SdkVersion': 'sample-python-requests',
#                'client-request-id': str(uuid.uuid4()),
#                'return-client-request-id': 'true'}
#     graphdata = MSGRAPH.get(endpoint, headers=headers).json()
#     return {'graphdata': graphdata, 'endpoint': endpoint,
#               'sample': 'Requests-OAuthlib'}


# @bottle.route('/static/<filepath:path>')
# def server_static(filepath):
#     """Handler for static files, used with the development server."""
#     root_folder = os.path.abspath(os.path.dirname(__file__))
#     return bottle.static_file(filepath, root=os.path.join(
#       root_folder, 'static'))


class MyWSGIRefServer(bottle.WSGIRefServer):  # ServerAdapter):
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


@cv.task_schema(Config(None, None).get_schema())
def task_oauth_authenticate(_, opt):
    """Authenticate.

    AUTHORITY_URL ending determines type of account that can be authenticated:
        /organizations = organizational accounts only
        /consumers = MSAs only (Microsoft Accounts: Live.com, Hotmail.com, etc)
        /common = allow both types of accounts
    """
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    global CONFIG, SERVER
    opt = dict(opt)
    opt.pop('task')
    CONFIG = Config(**opt)
    CONFIG.init_session()

    # bottle.run(app=bottle.app(), server='wsgiref', host=host, port=port)
    # Custom server can be shutdown
    app = bottle.app()
    SERVER = MyWSGIRefServer(host=CONFIG.host, port=CONFIG.port)
    try:
        app.run(server=SERVER)
    except Exception as exc:  # pylint: disable=broad-except
        _LOGGER.error(exc)
