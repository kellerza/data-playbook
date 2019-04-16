"""Tests for data.py"""
import logging

import pytest
import voluptuous as vol
import yaml

import dataplaybook.config_validation as cv
from dataplaybook import DataPlaybook
from dataplaybook.const import PlaybookError
from dataplaybook.data import DataEnvironment
from tests.common import load_module

_LOGGER = logging.getLogger(__name__)


@cv.task_schema({
    vol.Required('data'): vol.Any(dict, list),
}, target=1, kwargs=True)
def task_test_data(_, data):
    """Test data."""
    return data


def test_load_and_run():
    """Test starting from string, alias key('_') and target."""
    txt = """
        _: &v 111
        tasks:
          - task: test_data
            data: [{a: *v}]
            target: tab1
    """
    load_module(__file__)
    dpb = DataPlaybook(yaml_text=txt)
    assert '_' not in dpb.config, "alias subkey '_' not removed"
    assert list(dpb.config.keys()) == ['tasks', 'modules']
    assert dpb.config['tasks'] == [{
        'task': 'test_data',
        'data': [{'a': 111}],
        'target': 'tab1'
    }]

    assert 'tab1' not in dpb.tables
    dpb.run()
    assert 'tab1' in dpb.tables

    _LOGGER.debug(list(dpb.tables.items()))
    assert dpb.tables['tab1'] == [{'a': 111}]


@cv.task_schema({
    vol.Required('data'): vol.Any(dict, list),
}, kwargs=True)
def task_test_env(env, data):
    """Test data."""
    assert env['tab1'] == [{'a': 5}]

    assert isinstance(env, DataEnvironment)
    env['tab2'] = data


def test_env_to_function():
    """Test starting from string."""
    txt = """
        tasks:
          - task: test_data
            data: [{'a': 5}]
            target: tab1
          - task: test_env
            data: ['tab2 data']

    """
    load_module(__file__)
    dpb = DataPlaybook(yaml_text=txt)
    dpb.run()
    assert dpb.tables['tab2'] == ['tab2 data']


def test_bad_alias():
    """Test starting from string, alias key('_') and target."""
    txt = """
        _: &v 111
        tasks:
          - *not_v
    """
    with pytest.raises(yaml.composer.ComposerError):
        DataPlaybook(yaml_text=txt)
    # TODO: raise PlaybookError and handle correctly


@cv.task_schema({
}, target=1, kwargs=True)
def task_target_fail(_):
    """Test target fail."""
    raise PlaybookError


@cv.task_schema({
}, target=1, kwargs=True)
def task_target_fail_bad_params(_, bad, bad2):
    """Test target fail."""
    raise PlaybookError


def test_target_fail():
    """Test target fail."""
    load_module(__file__)

    dpb = DataPlaybook(yaml_text="""
        tasks:
          - task: target_fail
            target: tab1

    """)
    dpb.run()

    dpb = DataPlaybook(yaml_text="""
        tasks:
          - task: target_fail_bad_params
            target: tab1

    """)
    dpb.run()
    # TODO: imporve failures


@cv.task_schema({
}, target=1, kwargs=True)
def task_target_var(env):
    """Test target fail."""
    return {'a': 'var'}


def test_variables():
    """Test target fail."""
    load_module(__file__)

    dpb = DataPlaybook(yaml_text="""
        tasks:
          - task: target_var
            target: tab1
    """)
    dpb.run()

    assert dpb.tables.var == {'tab1': {'a': 'var'}}
