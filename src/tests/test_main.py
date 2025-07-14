"""Main tests."""

import unittest
from unittest.mock import Mock, patch

import pytest

from dataplaybook.__main__ import main as __main
from dataplaybook.main import (
    _ALL_PLAYBOOKS,
    ALL_TASKS,
    playbook,
    print_tasks,
    run_playbooks,
)

# from .conftest import import_folder


def test_print(capsys: pytest.CaptureFixture[str]) -> None:
    """Sample print."""
    # with import_folder("dataplaybook/tasks") as tasks:
    print_tasks()
    assert "read_excel" in ALL_TASKS
    captured = capsys.readouterr()
    # assert captured.out == "hello\n"
    assert "read_excel" in captured.err


def test_run_playbooks_true() -> None:
    """Test run."""
    with pytest.raises(SystemExit):
        __main()
    res = run_playbooks(dataplaybook_cmd=True)
    assert res == 0
    # atexit.unregister(run_playbooks)


class TestPlaybook(unittest.TestCase):
    """Test playbook decorator."""

    @patch("sys.exit")
    def test_default_playbook(self, mock_exit: Mock) -> None:
        """Test default playbook."""
        _ALL_PLAYBOOKS.clear()

        @playbook(default=True)
        def func1() -> None:
            pass

        @playbook(default=True)
        def func2() -> None:
            pass

        mock_exit.assert_called_with("Multiple default playbooks")

    def test_all_playbooks(self) -> None:
        """Test all playbooks."""
        _ALL_PLAYBOOKS.clear()

        @playbook()
        def func1() -> None:
            """Test function 1."""

        @playbook(name="func3")
        def func2() -> None:
            """Test function 2."""

        self.assertEqual(_ALL_PLAYBOOKS, {"func1": func1, "func3": func2})

    @patch("atexit.register")
    def test_run_playbooks(self, mock_register: Mock) -> None:
        """Test run playbooks."""
        _ALL_PLAYBOOKS.clear()

        @playbook(run=True)
        def func2() -> None:
            pass

        mock_register.assert_called_with(run_playbooks)
