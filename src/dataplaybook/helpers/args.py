"""CLI arguments."""

import argparse
from collections import abc
from importlib.metadata import version

import attrs


@attrs.define
class DPArg:
    """Dataplaybook arguments."""

    files: str = ""
    playbook: str = ""
    all: bool = False
    v: int = 0
    """Debug verbosity."""


def parse_args(
    *, dataplaybook_cmd: bool, default_playbook: str, playbooks: abc.Iterable[str]
) -> DPArg:
    """Parse dataplaybook CLI arguments."""
    ver = version("dataplaybook")
    parser = argparse.ArgumentParser(
        description=f"Data Playbook v{ver}. Playbooks for tabular data."
    )
    if dataplaybook_cmd:
        parser.add_argument("files", type=str, nargs="?", help="The playbook py file")
        parser.add_argument("--all", action="store_true", help="Load all tasks")

    parser.add_argument(
        "playbook",
        type=str,
        nargs="?",
        default=default_playbook,
        help=f"The playbook function name: {', '.join(playbooks)}",
    )
    parser.add_argument("-v", action="count", help="Debug level")

    res = DPArg()
    args = parser.parse_args(namespace=res)
    # if not args:
    #     sys.exit("No arguments supplied")
    if not dataplaybook_cmd:
        args.files = ""
        args.all = False
    return args
