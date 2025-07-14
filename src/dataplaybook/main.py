"""Dataplaybook tasks."""

import atexit
import logging
import os
import sys
import typing as t
from functools import partial, wraps
from inspect import Parameter, isgeneratorfunction, signature
from pathlib import Path

import attrs
from icecream import colorizedStderrPrint, ic

from dataplaybook.helpers.args import parse_args
from dataplaybook.helpers.env import DataEnvironment
from dataplaybook.helpers.typeh import repr_call, repr_signature, typechecked
from dataplaybook.utils import doublewrap, local_import_module
from dataplaybook.utils.logger import setup_logger

_LOGGER = logging.getLogger(__name__)


@attrs.define
class Task:
    """Task definition."""

    name: str = ""
    module: str = ""
    func: t.Callable | None = None
    gen: bool = False


ALL_TASKS: dict[str, Task] = {}
_ENV = DataEnvironment()


def print_tasks() -> None:
    """Print all_tasks."""
    mods: dict = {}
    for name, tsk in ALL_TASKS.items():
        mods.setdefault(tsk.module, []).append(f'{name} "{repr_signature(tsk.func)}"')
        mods[tsk.module].sort()

    for mod, fun in mods.items():
        colorizedStderrPrint(mod)
        colorizedStderrPrint("- " + "\n- ".join(fun))


def _add_task(task_function: t.Callable) -> None:
    """Add the task to ALL_TASKS."""
    newtask = Task(
        name=task_function.__name__,
        func=task_function,
        module=task_function.__module__,
        gen=isgeneratorfunction(task_function),
    )
    # Save the task
    if newtask.name in ALL_TASKS:
        if newtask.module == ALL_TASKS[newtask.name].module:
            return
        _LOGGER.warning(
            "Task %s (%s) already loaded, overwriting with %s (%s)",
            newtask.name,
            ALL_TASKS[newtask.name].module,
            newtask.name,
            newtask.module,
        )
    ALL_TASKS[newtask.name] = newtask


T = t.TypeVar("T")
P = t.ParamSpec("P")


def _run_task(
    *args: t.Any,
    task_function: t.Callable[P, T],
    **kwargs: t.Any,
) -> T:
    _LOGGER.info("Calling %s", repr_call(task_function, kwargs=kwargs))

    # Warning for explicit parameters
    if args:
        short = [str(a)[:20] for a in args]
        raise TypeError(f"Use explicit parameters, instead of {short}")

    try:
        value = typechecked(task_function)(*args, **kwargs)
    except Exception as err:
        _LOGGER.error(
            "Task %s raised %s: %s",
            task_function.__name__,
            type(err).__name__,
            err,
            # exc_info=err,
        )
        raise

    return value


def task(target: t.Callable[P, T]) -> t.Callable[t.Concatenate[P], T]:
    """Task wrapper."""
    sig = signature(target)
    notkw = [
        f"{k}=_" for k, p in sig.parameters.items() if p.kind != Parameter.KEYWORD_ONLY
    ]
    if notkw:
        msg = ", ".join(notkw)
        msg = (
            f"{target.__name__} should have keyword only-parameters: ("
            f"({msg}) --> (*, {msg})"
        )

        raise TypeError(msg)

    _add_task(target)
    return wraps(target)(partial(_run_task, task_function=target))


_ALL_PLAYBOOKS: dict[str, t.Callable] = {}
_DEFAULT_PLAYBOOK: str | None = None


@doublewrap
def playbook(
    target: t.Callable = lambda: print("@doublewrap"),
    name: str | None = None,
    default: bool = False,
    run: bool = False,
) -> t.Callable:
    """Verify parameters & execute task."""
    if default:
        global _DEFAULT_PLAYBOOK  # noqa: PLW0603
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


def run_playbooks(dataplaybook_cmd: bool = False) -> int:  # noqa: PLR0912, PLR0911
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
        import dataplaybook.tasks.all  # noqa: F401

    if args.v > 2:
        print_tasks()

    if not args.files:
        _LOGGER.info("Please specify a .py file to execute.")
        return -1

    cwd = Path.cwd()

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
            except Exception as err:
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
        except Exception as err:
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
