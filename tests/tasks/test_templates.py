"""Tests for jmespath.py"""
import dataplaybook.config_validation as cv
from dataplaybook import DataPlaybook
from tests.common import load_module


@cv.task_schema({}, target=1)
def task_load_test_data(env, opt):
    """Load test data."""
    return [
        {'k': 1, 'v': 'one'},
        {'k': 2, 'v': 'two'},
        {'k': '2', 'v': 'two string'},
    ]


def test_jmespath_task():
    """Test basic jmespath to variable."""
    load_module(__file__)

    dpb = DataPlaybook(yaml_text="""
        modules: [dataplaybook.tasks.templates]
        tasks:
          - task: load_test_data
            target: test

          - task: jmespath
            jmespath: "[?k==`2`].v | [0]"
            tables: test
            target: test2

          - task: jmespath
            jmespath: "test[?k==`2`].v"
            target: test3

          - task: jmespath
            jmespath: "test[?k=='2'].v"
            target: test_str

          - task: jmespath
            jmespath: "test[?k=='2'].v"
            target: test_str2
    """)
    dpb.run()
    assert dpb.tables['test'][0] == {'k': 1, 'v': 'one'}
    assert dpb.tables.var == {'test2': 'two'}
    assert dpb.tables.var.test2 == 'two'

    assert dpb.tables['test3'] == ['two']

    assert dpb.tables['test_str'] == ['two string']
    assert dpb.tables['test_str2'] == ['two string']


def test_templateSchema_jmespath():  # pylint: disable=invalid-name
    """Test basic jmespath to variable."""
    load_module(__file__)

    dpb = DataPlaybook(yaml_text="""
        modules: [dataplaybook.tasks.templates]
        tasks:
          - task: load_test_data
            target: test

          - task: set
            value: Normal return value
            target: test1

          - task: set
            value: jmespath test[?k==`2`].v | [0]
            target: test2
    """)
    dpb.run()
    assert dpb.tables['test'][0] == {'k': 1, 'v': 'one'}
    assert dpb.tables.var.test1 == 'Normal return value'
    assert dpb.tables.var.test2 == 'two'


def test_templateSchema_jinja():  # pylint: disable=invalid-name
    """Test basic jinja to variable."""
    load_module(__file__)

    dpb = DataPlaybook(yaml_text="""
        modules: [dataplaybook.tasks.templates]
        tasks:
          - task: load_test_data
            target: test

          - task: set
            value: Normal return value
            target: test1

          - task: set
            value: '{{ test[0].v }}'
            target: test0

          - task: set
            value: '{{ test[1].v }}'
            target: test2
    """)
    dpb.run()
    assert dpb.tables['test'][0] == {'k': 1, 'v': 'one'}
    assert dpb.tables.var.test1 == 'Normal return value'
    assert dpb.tables.var.test0 == 'one'
    assert dpb.tables.var.test2 == 'two'
