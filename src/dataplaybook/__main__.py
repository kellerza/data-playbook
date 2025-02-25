"""Dataplaybook script."""

import sys

from dataplaybook.main import run_playbooks


def main() -> int:
    """Execute a playbook."""
    sys.exit(run_playbooks(dataplaybook_cmd=True))


if __name__ == "__main__":
    main()
