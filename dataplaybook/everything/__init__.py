"""Query Voidtools' Everything Search for files."""
# Example:
# http://localhost:8881/?s=zz%20xls&j=1&path_column=1
# { "totalResults":25, "results":[ { "type":"file",
#   "name":"filename.xlsx", "path":"C:\\...." }
#
from collections import namedtuple
from pathlib import Path

import requests

SANE = (r"!c:\windows !appdata\ !\.git !\.vscode !_old\ !.lnk !~$"
        r" !C:\program !c:\$R")
SERVER = "http://localhost:8881"

Result = namedtuple('Result', ['total', 'files', 'folders'])
PathT = namedtuple('PathT', ['path', 'name'])


def _everything_params(*args, max_results):
    return {
        'j': 1, 'path_column': 1,
        's': ' '.join(args),
        'c': max_results
    }


def _everything_result(json, class_):
    """a."""
    result = {'total': -1, 'files': [], 'folders': [], }
    result['total'] = json['totalResults']
    for itm in json['results']:
        try:
            result[itm['type'] + 's'].append(class_(itm['path'], itm['name']))
        except KeyError as err:
            print(err)
    return Result(**result)


def get_files(*search, sane=True, max_results=50, class_=Path):
    """Get a list of files."""
    if sane is True:
        sane = SANE
    params = _everything_params(*search, sane, max_results=max_results)
    res = requests.get(SERVER, params=params)
    return _everything_result(res.json(), class_)
