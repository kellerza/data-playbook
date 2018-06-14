"""Datatask script."""
# import argparse
import argparse
import sys
import os
from pathlib import Path

from dataplaybook.data import DataPlaybook, setup_logger, loader
from dataplaybook.const import VERSION


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

    for file in files:
        if file.parent:
            os.chdir(file.parent)
        task = DataPlaybook(yaml_file=file.name)
        task.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
