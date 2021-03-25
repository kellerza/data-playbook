"""Import all available tasks."""
from dataplaybook.tasks import *  # noqa  pylint: disable=wildcard-import,unused-wildcard-import
from dataplaybook.tasks.ietf import *  # noqa  pylint: disable=wildcard-import,unused-wildcard-import
from dataplaybook.tasks.io_misc import *  # noqa  pylint: disable=wildcard-import,unused-wildcard-import
from dataplaybook.tasks.io_mongo import *  # noqa  pylint: disable=wildcard-import,unused-wildcard-import
from dataplaybook.tasks.io_pdf import *  # noqa  pylint: disable=wildcard-import,unused-wildcard-import
from dataplaybook.tasks.io_xlsx import *  # noqa  pylint: disable=wildcard-import,unused-wildcard-import
from dataplaybook.tasks.io_xml import *  # noqa  pylint: disable=wildcard-import,unused-wildcard-import

try:
    from dataplaybook.tasks.fuzzy import *  # noqa  pylint: disable=wildcard-import,unused-wildcard-import
except ImportError as err:
    print("Could not import 'dataplaybook.tasks.fuzzy':", err)
