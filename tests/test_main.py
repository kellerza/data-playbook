"""Main tests."""
import unittest
from unittest.mock import patch

import pytest

from dataplaybook.__main__ import main as __main
from dataplaybook.main import _ALL_PLAYBOOKS, playbook, print_tasks, run_playbooks


def test_print(capsys):
    """Sample print."""
    print_tasks()
    captured = capsys.readouterr()
    # assert captured.out == "hello\n"
    assert "read_excel" in captured.err


def test_run_playbooks_true():
    """Test run."""
    with pytest.raises(SystemExit):
        __main()
    res = run_playbooks(dataplaybook_cmd=True)
    assert res == 0
    # atexit.unregister(run_playbooks)


class TestPlaybook(unittest.TestCase):
    @patch("sys.exit")
    def test_default_playbook(self, mock_exit):
        _ALL_PLAYBOOKS.clear()

        @playbook(default=True)
        def func1():
            pass

        @playbook(default=True)
        def func2():
            pass

        mock_exit.assert_called_with("Multiple default playbooks")

    def test_all_playbooks(self):
        _ALL_PLAYBOOKS.clear()

        @playbook
        def func1():
            pass

        @playbook(name="func3")
        def func2():
            pass

        self.assertEqual(_ALL_PLAYBOOKS, {"func1": func1, "func3": func2})

    @patch("atexit.register")
    def test_run_playbooks(self, mock_register):
        _ALL_PLAYBOOKS.clear()

        @playbook(run=True)
        def func2():
            pass

        mock_register.assert_called_with(run_playbooks)
