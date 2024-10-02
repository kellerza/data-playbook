"""Dataplaybook tasks."""

import atexit
import logging
import os
import sys
import typing
from functools import wraps
from inspect import isgeneratorfunction, signature
from pathlib import Path
from typing import Any, Callable, Sequence

from icecream import colorizedStderrPrint, ic
from typeguard import _CallMemo, check_argument_types, check_return_type

from dataplaybook.const import Tables
from dataplaybook.helpers.args import parse_args
from dataplaybook.helpers.env import DataEnvironment
from dataplaybook.utils import doublewrap, local_import_module
from dataplaybook.utils.logger import setup_logger

_LOGGER = logging.getLogger(__name__)


ALL_TASKS: dict = {}
_ENV = DataEnvironment()


def print_tasks() -> None:
    """Print all_tasks."""

    def sign(func: Callable) -> str:
        sig = str(signature(func))
        sig = (
            sig.replace("typing.", "")
            .replace("Generator[dict[str, Any], NoneType, NoneType]", "RowDataGen")
            .replace("dict[str, Any]", "RowData")
            .replace(str(Tables).replace("typing.", ""), "Tables")
        )
        sig = sig.replace("dataplaybook.helpers.env.DataEnvironment", "DataEnvironment")
        # sig = sig.replace(str(TableXXX).replace("typing.", ""), "Table")
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
    type_hints = typing.get_type_hints(target)
    repr_args = [repr(a)[:50] for a in args]
    repr_kwargs = [f"{k}={v!r}" for k, v in kwargs.items()]
    repr_call = f"{target.__name__}({', '.join(repr_args + repr_kwargs)})"
    if "return" in type_hints:
        repr_call = f"_ = {repr_call}"
    _LOGGER.info("Calling %s", repr_call)


def _add_task(task_function: Callable, validator: Callable | None = None) -> None:
    """Add the task to ALL_TASKS."""

    # Save the task
    name = task_function.__name__
    if name in ALL_TASKS:
        _LOGGER.warning(
            "Task %s (%s) already loaded, overwriting with %s (%s)",
            name,
            ALL_TASKS[name]["module"],
            name,
            task_function.__module__,
        )
    ALL_TASKS[task_function.__name__] = {
        "func": task_function,
        "validator": validator,
        "gen": isgeneratorfunction(task_function),
        "module": task_function.__module__,
    }


T = typing.TypeVar("T")
P = typing.ParamSpec("P")


def _run_task(
    task_function: Callable[P, T],
    validator: Callable | None,
    *args: Any,
    **kwargs: Any,
) -> T:
    _repr_function(target=task_function, args=args, kwargs=kwargs)  # type:ignore

    # Warning for explicit parameters
    if args:
        short = [str(a)[:20] for a in args]
        _LOGGER.warning("Use explicit parameters, instead of %s", short)

    # Warning on parameter types
    call_memo = _CallMemo(task_function, args=args, kwargs=kwargs)
    try:
        check_argument_types(call_memo)
    except TypeError as err:
        _LOGGER.warning(err)

    if validator:
        validator(kwargs)

    try:
        value = task_function(*args, **kwargs)
    except Exception as err:
        _LOGGER.error(
            "Error while running task `%s` - %s",
            task_function.__name__,
            type(err).__name__,
            exc_info=err,
        )
        raise

    try:
        check_return_type(value, call_memo)
    except TypeError as err:
        _LOGGER.warning(
            "Unexpected return from task `%s`: %s", task_function.__name__, err
        )

    return value


def task(target: Callable[P, T]) -> Callable[P, T]:
    """Task wrapper."""

    @wraps(target)
    def task_wrapper(*args: Any, **kwargs: Any) -> T:
        return _run_task(target, None, *args, **kwargs)

    _add_task(target)
    return task_wrapper


def task_validate(*, validator: Callable) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Task wrapper with arguments."""

    def _wrapper(target: Callable[P, T]) -> Callable[P, T]:
        @wraps(target)
        def task_wrapper(*args: Any, **kwargs: Any) -> T:
            return _run_task(target, validator, *args, **kwargs)

        _add_task(target)
        return task_wrapper

    return _wrapper


K = typing.TypeVar("K", Callable, Callable)


# @doublewrap
# def task(
#     target: K | None = None,  # type: ignore
#     validator: Callable | None = None,
# ) -> K:
#     """Verify parameters & execute task."""

#     @wraps(target)  # type:ignore
#     def taskwrapper(*args: Any, **kwargs: Any) -> ATable:
#         return _run_task(target, validator, *args, **kwargs)  # type:ignore

#     if target:
#         _add_task(target, validator)

#     return taskwrapper


_ALL_PLAYBOOKS: dict[str, Callable] = {}
_DEFAULT_PLAYBOOK: str | None = None


@doublewrap
def playbook(
    target: Callable = None,  # type: ignore
    name: str | None = None,
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


def get_default_playbook() -> str:
    """Get the name of the default playbook, if any."""
    if _DEFAULT_PLAYBOOK:
        return _DEFAULT_PLAYBOOK
    if len(_ALL_PLAYBOOKS) == 1:
        return next(iter(_ALL_PLAYBOOKS))
    return ""


def run_playbooks(dataplaybook_cmd: bool = False) -> int:
    """Execute playbooks, or prompt for one."""
    if _EXECUTED:
        return 0
    _EXECUTED.append(True)

    args = parse_args(
        dataplaybook_cmd=dataplaybook_cmd,
        default_playbook=get_default_playbook(),
        playbooks=_ALL_PLAYBOOKS.keys(),
    )

    setup_logger()

    if args.all:
        import dataplaybook.tasks.all  # noqa pylint: disable=unused-import,import-outside-toplevel

    if args.v > 2:
        print_tasks()

    if not args.files:
        _LOGGER.info("Please specify a .py file to execute.")
        return -1

    cwd = os.getcwd()

    try:
        if dataplaybook_cmd:
            spath = Path(args.files).resolve()
            if not spath.exists():
                if spath.suffix != "" or not spath.with_suffix(".py").exists():
                    _LOGGER.error("%s not found", spath)
                    return -1
                spath = spath.with_suffix(".py")
            if spath.is_dir():
                _LOGGER.error("Please specify a file. %s is a folder.", spath)
                return -1

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
            if not args.playbook:
                _LOGGER.critical("No playbook found")
                return -1

        if args.playbook not in _ALL_PLAYBOOKS:
            _LOGGER.error(
                "Playbook %s not found in %s [%s]",
                args.playbook,
                args.files[0],
                ",".join(_ALL_PLAYBOOKS),
            )
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
