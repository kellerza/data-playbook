"""Dataplaybook tasks."""
import argparse
import atexit
from functools import wraps
from inspect import isgeneratorfunction, signature
import logging
from os import chdir
from pathlib import Path
import sys
from typing import get_type_hints

from icecream import colorizedStderrPrint, ic  # noqa pylint: disable=unused-import
from typeguard import _CallMemo, check_argument_types, check_return_type

from dataplaybook.const import VERSION, ATable, Table, Tables
from dataplaybook.utils import (
    DataEnvironment,
    doublewrap,
    local_import_module,
    setup_logger,
)

_LOGGER = logging.getLogger(__name__)


ALL_TASKS = {}
_ENV = DataEnvironment()


def print_tasks():
    """Print all_tasks."""

    def sign(func):
        sig = str(signature(func))
        sig = sig.replace(str(Tables).replace("typing.", ""), "Tables")
        sig = sig.replace(str(Table).replace("typing.", ""), "Table")
        return sig

    mods = {}
    for (name, tsk) in ALL_TASKS.items():
        mods.setdefault(tsk["module"], []).append(f'{name} "{sign(tsk["func"])}"')
        mods[tsk["module"]].sort()

    for (mod, fun) in mods.items():
        colorizedStderrPrint(mod)
        colorizedStderrPrint("- " + "\n- ".join(fun))
    # for mod_name, items in mods.items():
    #    _LOGGER.debug("%s: %s", mod_name, ", ".join(items))


def _repr_function(*, target, args, kwargs):
    """Function repr."""
    type_hints = get_type_hints(target)
    repr_args = [repr(a)[:50] for a in args]
    repr_kwargs = [f"{k}={v!r}" for k, v in kwargs.items()]
    repr_call = f"{target.__name__}({', '.join(repr_args + repr_kwargs)})"
    if "return" in type_hints:
        repr_call = f"_ = {repr_call}"
    _LOGGER.info("Calling %s", repr_call)


@doublewrap
def task(target=None, validator=None):  # noqa
    """Verify parameters & execute task."""

    @wraps(target)
    def taskwrapper(*args, **kwargs):
        _repr_function(target=target, args=args, kwargs=kwargs)

        # Warning for explicit parameters
        if args:
            short = [str(a)[:20] for a in args]
            _LOGGER.warning("Use explicit parameters, instead of %s", short)

        # Warning on parameter types
        call_memo = _CallMemo(target, args=args, kwargs=kwargs)
        try:
            check_argument_types(call_memo)
        except TypeError as err:
            _LOGGER.warning(err)

        if validator:
            validator(kwargs)

        try:
            value = target(*args, **kwargs)
        except Exception as err:
            _LOGGER.error(
                "Error while running task `%s` - %s: %s", name, type(err).__name__, err
            )
            raise

        if isgeneratorfunction(target) or (
            isinstance(value, list) and not isinstance(value, ATable)
        ):
            value = ATable(value)

        try:
            check_return_type(value, call_memo)
        except TypeError as err:
            _LOGGER.error(err)

        return value

    # Save the task
    name = target.__name__
    if name in ALL_TASKS:
        _LOGGER.error(
            "Task %s (%s) already loaded, overwriting with %s (%s)",
            name,
            ALL_TASKS[name]["module"],
            name,
            target.__module__,
        )
    ALL_TASKS[target.__name__] = {
        "func": target,
        "validator": validator,
        "gen": isgeneratorfunction(target),
        "module": target.__module__,
    }

    return taskwrapper


_ALL_PLAYBOOKS = {}
_DEFAULT_PLAYBOOK = None


@doublewrap
def playbook(target=None, name=None, default=False, run=False):
    """Verify parameters & execute task."""

    if default:
        global _DEFAULT_PLAYBOOK
        if _DEFAULT_PLAYBOOK:
            sys.exit("Multiple default playbooks")
        _DEFAULT_PLAYBOOK = name or target.__name__

    _ALL_PLAYBOOKS[name or target.__name__] = target

    if run:
        atexit.register(run_playbooks)

    return target


_EXECUTED = False


def get_default_playbook():
    """Get the name of the defualt playbook, if any."""
    if _DEFAULT_PLAYBOOK:
        return _DEFAULT_PLAYBOOK
    if len(_ALL_PLAYBOOKS) == 1:
        return next(iter(_ALL_PLAYBOOKS))
    return None


def run_playbooks(dataplaybook_cmd=False):
    """Execute playbooks, or prompt for one."""
    global _EXECUTED
    if _EXECUTED:
        return
    _EXECUTED = True

    parser = argparse.ArgumentParser(
        description="Data Playbook v{}. Playbooks for tabular data.".format(VERSION)
    )
    if dataplaybook_cmd:
        parser.add_argument("files", type=str, nargs=1, help="The playbook py file")
        parser.add_argument("--all", action="store_true", help="Load all tasks")

    parser.add_argument(
        "playbook",
        type=str,
        nargs="?",
        default=get_default_playbook(),
        help=f"The playbook function name: {', '.join(_ALL_PLAYBOOKS)}",
    )
    parser.add_argument("-v", action="count", help="Debug level")
    args = parser.parse_args()

    setup_logger()

    if args.all:
        import dataplaybook.tasks.all  # noqa pylint: disable=unused-import,import-outside-toplevel

    if args.v and args.v > 2:
        print_tasks()

    if dataplaybook_cmd:
        spath = Path(args.files[0]).resolve()
        if not spath.exists():
            if spath.suffix != "" or not spath.with_suffix(".py").exists():
                _LOGGER.error("%s not found", spath)
                sys.exit(-1)
            spath = spath.with_suffix(".py")

        _LOGGER.info("Loading: %s (%s)", spath.name, spath.parent)
        chdir(spath.parent)
        try:
            local_import_module(spath.stem)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Unable to import %s: %s", spath.stem, err)
            sys.exit(-1)

    else:
        # Ensure we are in the calling script's folder
        chdir(Path(sys.argv[0]).resolve().parent)

    if not args.playbook:
        args.playbook = get_default_playbook()

    if args.playbook not in _ALL_PLAYBOOKS:
        _LOGGER.error("Playbook %s not found in %s", args.playbook, args.files[0])
        sys.exit(-1)

    try:
        retval = _ALL_PLAYBOOKS[args.playbook](_ENV)
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error(
            "Error while running playbook '%s' - %s: %s",
            args.playbook,
            type(err).__name__,
            err,
        )
        raise err
    else:
        if args.v:
            ic(_ENV)

        sys.exit(retval)
