"""Tests for jmespath.py"""
# import dataplaybook.tasks as tasks
import dataplaybook.config_validation as cv
from dataplaybook import DataPlaybook
from tests.common import load_module


@cv.task_schema({}, target=1)
def task_load_test_data(env, opt):
    """Build a lookup table (unique key & columns) and removing the columns."""
    return [
        {'k': 1, 'v': 'one'},
        {'k': 2, 'v': 'two'},
        {'k': '2', 'v': 'two string'},
    ]


def test_jmespath():
    """Test basic jmespath to variable."""
    load_module(__file__)

    dpb = DataPlaybook(yaml_text="""
        modules: [dataplaybook.tasks.jmespath]
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
