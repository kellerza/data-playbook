"""XLSX tests."""
from unittest.mock import MagicMock

from dataplaybook import DataPlaybook
# from dataplaybook.tasks import io_xlsx


def test_read__migrate_config():
    """Test read."""
    dpb = DataPlaybook(modules=__name__, yaml_text="""
        modules: [dataplaybook.tasks.io_xlsx]
        tasks:
          - task: read_excel
            file: a.xlsx
            target: test
          - read_excel:
              file: a.xlsx
              default_sheet: test

          - task: read_excel
            file: a.xlsx
            sheet: sh1
            target: test
          - read_excel:
              file: a.xlsx
              sheets:
                - name: sh1
                  target: test
    """)
    mock = MagicMock()
    dpb.all_tasks['read_excel'].function = mock
    dpb.run()
    mock.assert_called()

    tasks = dpb.config['tasks']
    assert tasks[0] == tasks[1]
    assert tasks[2] == tasks[3]


def test_write__migrate_config():
    """Test read."""
    dpb = DataPlaybook(modules=__name__, yaml_text="""
        modules: [dataplaybook.tasks.io_xlsx]
        tasks:
          - task: write_excel
            file: a.xlsx
            ensure_string: ['a', 'b']
          - write_excel:
              file: a.xlsx
    """)
    mock = MagicMock()
    dpb.all_tasks['write_excel'].function = mock
    dpb.run()
    mock.assert_called()

    tasks = dpb.config['tasks']

    assert tasks[0] == {'write_excel': {'file': 'a.xlsx', 'header': []}}
    assert tasks[0] == tasks[1]
