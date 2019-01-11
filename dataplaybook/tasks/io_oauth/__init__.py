"""IO Oauth."""
import logging

import voluptuous as vol

import dataplaybook.config_validation as cv
from dataplaybook.tasks.io_oauth.oauth_session import Session
from dataplaybook.tasks.io_oauth.oauth_server import start

_LOGGER = logging.getLogger(__name__)
SES = None


@cv.task_schema(Session.validation_schema())
def task_oauth_authenticate(_, opt):
    """Authenticate.

    AUTHORITY_URL ending determines type of account that can be authenticated:
        /organizations = organizational accounts only
        /consumers = MSAs only (Microsoft Accounts: Live.com, Hotmail.com, etc)
        /common = allow both types of accounts
    """
    opt = dict(opt)
    opt.pop('task')

    global SES
    SES = Session(**opt)
    start(SES)

    # from pathlib import Path
    # home = str(Path.home())


@cv.task_schema({
    vol.Required('url'): str,
}, kwargs=True, target=True)
def task_oauth_request(_, url):
    """Retrieve a URL."""
    json = SES.get(url, {'expand': 'fields'})

    res = [v['fields'] for v in json['value']]
    return res
