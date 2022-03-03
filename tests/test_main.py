"""Main tests."""
import atexit

import pytest

import dataplaybook.main as main  # noqa # pylint: disable=unused-import
from dataplaybook.__main__ import main as __main


def test_print():
    """Sample print."""
    main.print_tasks()


def test_run_playbooks_true():
    """Test run."""
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        __main()  # run_playbooks(True)
    assert pytest_wrapped_e.type == SystemExit
    # assert pytest_wrapped_e.value.code == -1
    atexit.unregister(main.run_playbooks)


# def test_run_playbooks():
#     with pytest.raises(SystemExit) as pytest_wrapped_e:
#         main.run_playbooks()
#     assert pytest_wrapped_e.type == SystemExit
#     assert pytest_wrapped_e.value.code == -1
