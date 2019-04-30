"""Test io_mongo."""
from unittest.mock import MagicMock

from dataplaybook import DataPlaybook
from dataplaybook.tasks import io_mongo


def test_db_schema_post_validator():
    """Test read."""
    dpb = DataPlaybook(modules=__name__, yaml_text="""
        modules: [dataplaybook.tasks.io_mongo]
        tasks:
          - read_mongo:
              set_id: t1
              db: db://localhost:27027/text/text
            target: test
          - write_mongo:
              set_id: t1
              db: db://localhost:27027/text/text
            tables: test
    """)
    mock = MagicMock()
    dpb.all_tasks['read_mongo'].function = mock
    dpb.all_tasks['write_mongo'].function = mock
    dpb.run()
    mock.assert_called()

    tasks = dpb.config['tasks']
    assert len(tasks[0]) == 2
    mdb = io_mongo.MongoURI.from_string(
        'db://localhost:27027/text/text/t1')
    assert tasks[0] == {
        'read_mongo': {'db': mdb},
        'target': 'test'
    }

    assert tasks[1] == {
        'write_mongo': {'db': mdb},
        'tables': ['test'],
    }
