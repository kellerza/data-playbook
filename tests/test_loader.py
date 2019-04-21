"""Test loader functions."""
import logging
from unittest.mock import patch

import dataplaybook.config_validation as cv
from dataplaybook import loader

_LOGGER = logging.getLogger(__name__)


def test_load_yaml():
    yaml = "a: 1"
    res = loader.load_yaml(text=yaml)
    assert res['a'] == 1

    with patch('dataplaybook.loader.Path'), \
            patch('dataplaybook.loader.yaml.load'):
        loader.load_yaml()
    # TODO: does not really test yet


@cv.task_schema({
}, kwargs=True)
def task_test_empty_task(env):
    """Blank test task."""


def test_remove():
    """Remove modules."""
    all_tasks = loader.TaskDefs()
    all_tasks.load_module(__name__)
    assert all_tasks, f"Nothing loaded from {__name__}"
    _LOGGER.debug(len(all_tasks))
    all_tasks.remove_module(__name__)
    assert not all_tasks


# def test__find_file():
#     with patch('dataplaybook.everything.search') as sss:
#         sss.return_value = cv.AttrDict(
#             {'files': [Path(__file__)]})
#         fff = loader._find_file
#         assert fff ==Path(__file__)
