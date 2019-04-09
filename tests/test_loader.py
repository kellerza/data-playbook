import logging
from pathlib import Path
from unittest.mock import patch

import voluptuous as vol

import dataplaybook.config_validation as cv
from dataplaybook import loader
from dataplaybook.loader import TASKS
from dataplaybook.tasks import task_print
from tests.common import load_module

_LOGGER = logging.getLogger(__name__)


def test_task():
    """Test the Tasks class."""
    tsk = loader.Task('print', task_print, module='test_loader')
    assert tsk.schema  # propoerty
    assert isinstance(tsk.schema, vol.All)
    # TODO: assert "tasks" in str(tsk.module)


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
    start_l = len(TASKS.keys())
    load_module(__file__)
    assert len(TASKS) > start_l
    _LOGGER.debug(len(TASKS))
    loader.remove_module(Path(__file__).stem)
    assert len(TASKS) == start_l


# def test__find_file():
#     with patch('dataplaybook.everything.search') as sss:
#         sss.return_value = cv.AttrDict(
#             {'files': [Path(__file__)]})
#         fff = loader._find_file
#         assert fff ==Path(__file__)
