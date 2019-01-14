"""IO Oauth."""
import logging

import voluptuous as vol

import dataplaybook.config_validation as cv
from dataplaybook.tasks.io_oauth.oauth_server import start
from O365 import Account

_LOGGER = logging.getLogger(__name__)
ACC = None

DEFAULT_SCOPES = ['User.read', 'Sites.Read.All']


@cv.task_schema({
    vol.Required('client_id'): str,
    vol.Required('client_secret'): str,
    vol.Required('scopes', default=DEFAULT_SCOPES): vol.All(
        cv.ensure_list, [str]),
}, kwargs=True)
def task_oauth_authenticate(
        _, client_id, client_secret, scopes=None):
    """Authenticate if required."""
    global ACC
    ACC = Account((client_id, client_secret),
                  scopes=(scopes or DEFAULT_SCOPES))
    try:
        ACC.connection.get_session()
    except RuntimeError:
        # Need to get a new token
        start(ACC.connection)


@cv.task_schema({
    vol.Required('url'): str,
}, kwargs=True, target=True)
def task_oauth_request(_, url):
    """Retrieve a URL."""
    res = ACC.connection.get(url, {'expand': 'fields'})
    json = res.json()

    tres = [v['fields'] for v in json['value']]
    return tres
