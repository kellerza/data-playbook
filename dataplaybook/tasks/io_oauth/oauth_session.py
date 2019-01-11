"""Requests-OAuthlib sample for Microsoft Graph.

Uses Authorization code grant

https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#web-application-flow

 """

import logging
import uuid

import attr
import voluptuous as vol
from requests_oauthlib import OAuth2Session

import dataplaybook.config_validation as cv

_LOGGER = logging.getLogger(__name__)


@attr.s(slots=True)
class Session(object):
    """Oauth config."""
    client_id = attr.ib()
    client_secret = attr.ib()
    # https://sharepoint.stackexchange.com/a/237202
    scopes = attr.ib(default=['User.read', 'Sites.Read.All'],
                     validator=attr.validators.instance_of(list))
    port = attr.ib(default=5000)
    host = attr.ib(default='localhost')
    authority_url = attr.ib(
        default="https://login.microsoftonline.com/organizations")
    url_endpoint_auth = attr.ib(default="/oauth2/v2.0/authorize")
    url_endpoint_token = attr.ib(default="/oauth2/v2.0/token")

    session = attr.ib(init=False)  # type: OAuth2Session
    authorization_url = attr.ib(init=False)  # type: str

    def validation_schema(self=None):
        """Generate the task schema with defaults from Config instance."""
        if self is None:
            self = Session(None, None)
        return {
            vol.Required('client_id'): str,
            vol.Required('client_secret'): str,
            vol.Required('scopes', default=self.scopes): vol.All(
                cv.ensure_list, [str]),
            vol.Optional('authority_url', default=self.authority_url): str,
            vol.Optional('url_endpoint_auth',
                         default=self.url_endpoint_auth): str,
            vol.Optional('url_endpoint_token',
                         default=self.url_endpoint_token): str,
            vol.Optional('host', default=self.host): str,
            vol.Optional('port', default=self.port): int
        }

    def __attrs_post_init__(self):
        """Initialize the requests session."""
        redirect_url = "http://{}:{}/login/authorized".format(
            self.host, self.port)

        self.session = OAuth2Session(
            self.client_id,
            scope=self.scopes,
            redirect_uri=redirect_url
        )

        self.authorization_url, self.session.auth_state = \
            self.session.authorization_url(
                self.authority_url + self.url_endpoint_auth,
                access_type="offline",
                prompt="select_account"
            )
        # Visit the authorization_url and send thecallback UR

    def fetch_token(self, authorization_response):
        """Fetch the Token."""
        self.session.fetch_token(
            self.authority_url + self.url_endpoint_token,
            client_secret=self.client_secret,
            authorization_response=authorization_response
        )

    def get(self, url, params=None):
        """Request some json from the oauth endpoint."""
        headers = {
            'client-request-id': str(uuid.uuid4()),
            'return-client-request-id': 'true',
            'Accept': 'application/json'
        }
        res = self.session.get(url, headers=headers, params=params or {})
        print(res, dir(res))
        print('json:', res.json())
        return res.json()
