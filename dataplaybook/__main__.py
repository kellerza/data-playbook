"""Datatask script."""
import argparse
import os
import sys
from pathlib import Path

import voluptuous as vol

from dataplaybook.const import VERSION, PlaybookError
from dataplaybook import DataPlaybook
from dataplaybook.utils import setup_logger, set_logger_level


def main():
    """Execute playbook file."""
    parser = argparse.ArgumentParser(
        description="Data Playbook v{}. Playbooks for tabular data."
        .format(VERSION))
    parser.add_argument(
        'files', type=str, nargs='+', help='The playbook yaml file')
    args = parser.parse_args()

    files = [Path(fn) for fn in args.files]

    for file in files:
        if not file.exists():
            print("File {} not found".format(file))
            return 1

    setup_logger()
    set_logger_level({
        'dataplaybook.loader': 'info',
    })

    extra_modules = [
        'dataplaybook.tasks',
        'dataplaybook.tasks.templates',
        'dataplaybook.tasks.io_xlsx',
        'dataplaybook.tasks.io_misc'
    ]

    tasks = []
    for file in files:
        if file.parent:
            os.chdir(file.parent)
        try:
            tasks.append(DataPlaybook(
                modules=extra_modules, yaml_file=file.name))
        except PlaybookError:
            return 1
        except vol.MultipleInvalid as exc:
            print('Please fix validation errors in {} - {}'.format(
                file.name, str(exc)))
            return 1

    for task in tasks:
        task.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
