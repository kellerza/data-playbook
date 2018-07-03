"""Datatask script."""
import argparse
import os
import sys
from pathlib import Path

import voluptuous as vol

from dataplaybook.const import VERSION
from dataplaybook.data import DataPlaybook, loader, setup_logger


def main():
    """Execute playbook file."""
    parser = argparse.ArgumentParser(
        description="Data Playbook v{}. Playbooks for tabular data."
        .format(VERSION))
    parser.add_argument(
        'files', type=str, nargs='+', help='The playbook yaml file')
    # parser.add_argument(
    #    '-v', '--version', action='store_true', help="Show version.")
    args = parser.parse_args()

    files = [Path(fn) for fn in args.files]

    for file in files:
        if not file.exists():
            print("File {} not found".format(file))
            return 1

    setup_logger()
    loader.load_module('dataplaybook.tasks')
    loader.load_module('dataplaybook.tasks.io_xlsx')
    loader.load_module('dataplaybook.tasks.io_misc')

    tasks = []
    for file in files:
        if file.parent:
            os.chdir(file.parent)
        try:
            tasks.append(DataPlaybook(yaml_file=file.name))
        except vol.MultipleInvalid:
            print('Please fix validation errors in {}'.format(file.name))
            return 1

    for task in tasks:
        task.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
