# """IO Oauth."""
# import logging

# import voluptuous as vol
# from O365 import Account
# from O365.connection import Connection
# from O365.utils.token import FileSystemTokenBackend
# from typing import Optional, List

# from dataplaybook import task, Table
# import dataplaybook.config_validation as cv
# from dataplaybook.tasks.io_oauth.oauth_server import start

# _LOGGER = logging.getLogger(__name__)
# CON = None

# DEFAULT_SCOPES = ["offline_access", "User.read", "Sites.Read.All"]


# @task(
#     {
#         vol.Required("client_id"): str,
#         vol.Required("client_secret"): str,
#         vol.Required("scopes", default=DEFAULT_SCOPES): vol.All(cv.ensure_list, [str]),
#     }
# )
# def oauth_authenticate(
#     client_id: str, client_secret: str, scopes: Optional[List[str]] = None
# ):
#     """Authenticate if required."""
#     global CON
#     tbe = FileSystemTokenBackend()
#     CON = Connection(
#         (client_id, client_secret), scopes=(scopes or DEFAULT_SCOPES), token_backend=tbe
#     )
#     try:
#         CON.get_session(load_token=True)
#     except RuntimeError:
#         # Need to get a new token
#         start(CON)


# LIST_SCHEMA = vol.Schema(
#     {
#         vol.Required("value"): vol.Schema(
#             [vol.Schema({vol.Required("fields"): dict}, extra=vol.ALLOW_EXTRA)]
#         )
#     },
#     extra=vol.ALLOW_EXTRA,
# )
# EXCEL_SCHEMA = vol.Schema(
#     {vol.Required("values"): vol.Schema([vol.Schema(list)])}, extra=vol.ALLOW_EXTRA
# )


# def _async_oauth_request(json):
#     """Non I/O logic of task_oauth_request. Pass in json, yields rows"""
#     logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.WARNING)

#     schema_errors = []

#     try:
#         LIST_SCHEMA(json)
#     except vol.MultipleInvalid as err:
#         schema_errors.append("LIST_SCHEMA {}".format(err))
#     else:
#         for row in json["value"]:
#             res = row["fields"]
#             # slugify headers
#             res = {cv.util_slugify(k): v for k, v in res.items()}
#             # res['@odata_etag'] = res.pop('@odata.etag', None)
#             yield res
#         return

#     try:
#         EXCEL_SCHEMA(json)
#     except vol.MultipleInvalid as err:
#         schema_errors.append("EXCEL_SCHEMA {}".format(err))
#     else:
#         rows = json["values"]

#         headers = rows.pop(0)
#         # slugify headers
#         headers = [cv.util_slugify(v) for v in headers]
#         for row in rows:
#             if any(row):
#                 yield {k: v for k, v in zip(headers, row)}
#         return

#     _LOGGER.error(
#         "No schema matched: %s --- on text: %s", schema_errors, str(json)[:500]
#     )


# @task({vol.Required("url"): str})
# def oauth_request(url) -> Table:
#     """Retrieve a URL."""
#     res = CON.get(url, {"expand": "fields"})
#     json = res.json()
#     yield from _async_oauth_request(json)
#     yield {"response": str(json)}


# @task({vol.Required("filename"): str})
# def spo_find_file(filename) -> Table:
#     """Retrieve a URL."""
#     # storage = ACC.storage()
#     # for drive in storage.get_drives():
#     #     for file in drive.search(filename):
#     #         yield {
#     #             "drive": str(drive),
#     #             "file": str(file),
#     #             "id": file.object_id,
#     #         }

#     spo = Account(con=CON).sharepoint()
#     sites = []
#     # sites = spo.search_site('emea-ion-tech')
#     sites.append(spo.get_site("nokia.sharepoint.com", "/sites/emea-ion-tech"))

#     for site in sites:
#         yield {"site": str(site), "site_id": site.object_id}
#         # drive = site.get_default_document_library()
#         # #  --> seems to be personal Onedrive
#         for drive in site.list_document_libraries():
#             # for drive in (site.get_default_document_library(),):
#             yield {"drive": str(drive), "drive_id": drive.object_id}
#             for file in drive.search(filename):
#                 parent = file.get_parent()
#                 yield {
#                     "drive": str(drive),
#                     "folder": str(parent),
#                     "file": str(file),
#                     "id": file.object_id,
#                 }


# # @task({vol.Required("filename"): str})
# # def spo_read_excel(url) -> Table:
# #     """Retrieve a URL."""
# #     res = Account(con=CON).get_drive()
# #     # .get(url, {'expand': 'fields'})
# #     json = res.json()

# #     tres = [v["fields"] for v in json["value"]]
# #     return tres
