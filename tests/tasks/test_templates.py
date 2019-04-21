"""Tests for jmespath.py"""
import dataplaybook.config_validation as cv
from dataplaybook import DataPlaybook


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
    dpb = DataPlaybook(modules=__name__, yaml_text="""
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
    dpb = DataPlaybook(modules=__name__, yaml_text="""
        modules: [dataplaybook.tasks.templates]
        tasks:
          - task: load_test_data
            target: test

          - set:
              test1: Normal return value
              test2: jmespath test[?k==`2`].v | [0]
    """)
    dpb.run()
    assert dpb.tables['test'][0] == {'k': 1, 'v': 'one'}
    assert dpb.tables.var.test1 == 'Normal return value'
    assert dpb.tables.var.test2 == 'two'


def test_templateSchema_jinja():  # pylint: disable=invalid-name
    """Test basic jinja to variable."""
    dpb = DataPlaybook(modules=__name__, yaml_text="""
        modules: [dataplaybook.tasks.templates]
        tasks:
          - task: load_test_data
            target: test

          - set:
              test1: Normal return value
              test0: '{{ test[0].v }}'
              test2: '{{ test[1].v }}'
    """)
    dpb.run()
    assert dpb.tables['test'][0] == {'k': 1, 'v': 'one'}
    assert dpb.tables.var.test1 == 'Normal return value'
    assert dpb.tables.var.test0 == 'one'
    assert dpb.tables.var.test2 == 'two'
