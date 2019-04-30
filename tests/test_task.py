"""Config Validaiton Tests."""
from dataplaybook.task import TaskDef, _migrate_task
from dataplaybook.tasks import task_print


def test_task():
    """Test the TasksDef class."""
    tsk = TaskDef('print', task_print, module='test_loader')
    assert tsk.opt_schema
    assert isinstance(tsk.opt_schema, dict)
    # TODO: assert "tasks" in str(tsk.module)


def test_migrate_task():
    """Test migrate_task."""
    opt = {
        'var1': 1,
        'var2': '2',
        'debug': True,
    }
    task = dict(task='some', **opt)

    new = _migrate_task(task)
    assert list(new.keys()) == ['some']
    assert new['some'] == opt

    task['debug*'] = True
    new = _migrate_task(task)
    assert list(new.keys()) == ['some', 'debug']
    assert new['some'] == opt

    task['tables'] = 'some table'
    task['target'] = 'target'
    new = _migrate_task(task)
    assert list(new.keys()) == ['some', 'tables', 'target', 'debug']
    assert new['some'] == opt
