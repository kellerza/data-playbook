"""Dataplaybook tasks."""
import argparse
import atexit
import logging
import os
import sys
from functools import wraps
from inspect import isgeneratorfunction, signature
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, Union, get_type_hints

from icecream import colorizedStderrPrint, ic  # noqa pylint: disable=unused-import
from typeguard import _CallMemo, check_argument_types, check_return_type

from dataplaybook.const import VERSION, ATable, Table, Tables
from dataplaybook.helpers import DataEnvironment
from dataplaybook.utils import doublewrap, local_import_module
from dataplaybook.utils.logger import setup_logger

_LOGGER = logging.getLogger(__name__)


ALL_TASKS: dict = {}
_ENV = DataEnvironment()


def print_tasks() -> None:
    """Print all_tasks."""

    def sign(func: Callable) -> str:
        sig = str(signature(func))
        sig = sig.replace(str(Tables).replace("typing.", ""), "Tables")
        sig = sig.replace(str(Table).replace("typing.", ""), "Table")
        return sig

    mods: dict = {}
    for name, tsk in ALL_TASKS.items():
        mods.setdefault(tsk["module"], []).append(f'{name} "{sign(tsk["func"])}"')
        mods[tsk["module"]].sort()

    for mod, fun in mods.items():
        colorizedStderrPrint(mod)
        colorizedStderrPrint("- " + "\n- ".join(fun))
    # for mod_name, items in mods.items():
    #    _LOGGER.debug("%s: %s", mod_name, ", ".join(items))


def _repr_function(*, target: Callable, args: Sequence, kwargs: dict) -> None:
    """Represent the caller."""
    type_hints = get_type_hints(target)
    repr_args = [repr(a)[:50] for a in args]
    repr_kwargs = [f"{k}={v!r}" for k, v in kwargs.items()]
    repr_call = f"{target.__name__}({', '.join(repr_args + repr_kwargs)})"
    if "return" in type_hints:
        repr_call = f"_ = {repr_call}"
    _LOGGER.info("Calling %s", repr_call)


@doublewrap
def task(
    target: Callable = None,  # type: ignore
    validator: Optional[Callable] = None,
) -> Callable:
    """Verify parameters & execute task."""

    @wraps(target)
    def taskwrapper(*args: Any, **kwargs: Any) -> Union[ATable, Any]:
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

        if isgeneratorfunction(target):
            value = ATable(value)

        try:
            check_return_type(value, call_memo)
        except TypeError as err:
            _LOGGER.error(err)

        if isinstance(value, list) and not isinstance(value, ATable):
            value = ATable(value)

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


_ALL_PLAYBOOKS: dict[str, Callable] = {}
_DEFAULT_PLAYBOOK: Optional[str] = None


@doublewrap
def playbook(
    target: Callable = None,  # type: ignore
    name: Optional[str] = None,
    default: bool = False,
    run: bool = False,
) -> Callable:
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


_EXECUTED: list[bool] = []


def get_default_playbook() -> Optional[str]:
    """Get the name of the default playbook, if any."""
    if _DEFAULT_PLAYBOOK:
        return _DEFAULT_PLAYBOOK
    if len(_ALL_PLAYBOOKS) == 1:
        return next(iter(_ALL_PLAYBOOKS))
    return None


def _parseargs(dataplaybook_cmd: bool) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Data Playbook v{VERSION}. Playbooks for tabular data."
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
    if not args:
        sys.exit("No arguments supplied")
    if not dataplaybook_cmd:
        args.files = [""]
        args.all = False
    return args


def run_playbooks(dataplaybook_cmd: bool = False) -> int:
    """Execute playbooks, or prompt for one."""
    if _EXECUTED:
        return 0
    _EXECUTED.append(True)

    args = _parseargs(dataplaybook_cmd)

    setup_logger()

    if args.all:
        import dataplaybook.tasks.all  # noqa pylint: disable=unused-import,import-outside-toplevel

    if args.v and args.v > 2:
        print_tasks()

    cwd = os.getcwd()

    try:
        if dataplaybook_cmd:
            spath = Path(args.files[0]).resolve()
            if not spath.exists():
                if spath.suffix != "" or not spath.with_suffix(".py").exists():
                    _LOGGER.error("%s not found", spath)
                    return -1
                spath = spath.with_suffix(".py")

            _LOGGER.info("Loading: %s (%s)", spath.name, spath.parent)
            os.chdir(spath.parent)
            try:
                local_import_module(spath.stem)
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error("Unable to import %s: %s", spath.stem, err)
                return -1

        else:
            # Ensure we are in the calling script's folder
            os.chdir(Path(sys.argv[0]).resolve().parent)

        if not args.playbook:
            args.playbook = get_default_playbook()

        if args.playbook not in _ALL_PLAYBOOKS:
            _LOGGER.error("Playbook %s not found in %s", args.playbook, args.files[0])
            return -1

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

        if args.v:
            ic(_ENV)

        return int(retval) if retval else 0
    finally:
        os.chdir(cwd)
