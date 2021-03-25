"""Dataplaybook tasks."""
import argparse
import atexit
from functools import wraps
from inspect import isgeneratorfunction, signature
import logging
import sys
from typing import get_type_hints

from icecream import colorizedStderrPrint, ic  # noqa pylint: disable=unused-import
from typeguard import _CallMemo, check_argument_types, check_return_type
from varname import VarnameRetrievingError, varname

from dataplaybook.const import VERSION, Table, Tables, ATable
from dataplaybook.utils import DataEnvironment, setup_logger

_LOGGER = logging.getLogger(__name__)


ALL_TASKS = {}
ENV = DataEnvironment()


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


def _repr_function(*, target, args, kwargs, var_name, logs):
    """Function repr."""
    type_hints = get_type_hints(target)
    repr_args = [repr(a) for a in args]
    repr_kwargs = [f"{k}={v!r}" for k, v in kwargs.items()]
    repr_call = f"{target.__name__}({', '.join(repr_args + repr_kwargs)})"
    if "return" in type_hints:
        repr_call = f"{var_name} = {repr_call}"
        if var_name is None:
            logs.append(
                (logging.ERROR, "The variable's return value should be assigned")
            )
    logs.insert(0, (logging.INFO, f"Calling {repr_call})"))


def task(_target=None, *, validator=None):  # noqa
    """Verify parameters & execute task."""

    def _target_deco(target):
        @wraps(target)
        def taskwrapper(*args, info=None, **kwargs):
            logs = []

            if info:
                _LOGGER.info(info)

            if args:
                logs.append(
                    (logging.WARNING, f"Use explicit parameters, instead of {args}")
                )

            call_memo = _CallMemo(target, args=args, kwargs=kwargs)
            try:
                check_argument_types(call_memo)
            except TypeError as err:
                _LOGGER.error(err)

            if validator:
                validator(kwargs)

            var_name = None
            try:
                var_name = varname()
            except VarnameRetrievingError:
                pass

            _repr_function(
                target=target, var_name=var_name, args=args, kwargs=kwargs, logs=logs
            )

            for (lvl, msg) in logs:
                _LOGGER.log(lvl, msg)

            value = target(*args, **kwargs)

            if isgeneratorfunction(target) or (
                isinstance(value, list) and not isinstance(value, ATable)
            ):
                value = ATable(value)

            if var_name:
                ENV[var_name] = value
                if hasattr(value, name):
                    value.name = var_name

            try:
                check_return_type(value, call_memo)
            except TypeError as err:
                _LOGGER.error(err)

            return value

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
            # "validator": validator,
            "gen": isgeneratorfunction(target),
            "module": target.__module__,
        }
        # ic(target, dir(target))

        return taskwrapper

    return _target_deco if _target is None else _target_deco(_target)


_ALL_PLAYBOOKS = {}
_DEFAULT_PLAYBOOK = None


def playbook(_target=None, *, default=False, run=False):
    """Verify parameters & execute task."""

    def _target_deco(target):
        """Mark a playbook or run a playbook."""
        if target is None:
            run()

        # @wraps(target)
        # def playbookwrapper(*args, info=None, **kwargs):
        #    pass

        if default:
            global _DEFAULT_PLAYBOOK
            if _DEFAULT_PLAYBOOK:
                sys.exit("Multiple default playbooks")
            _DEFAULT_PLAYBOOK = target.__name__

        _ALL_PLAYBOOKS[target.__name__] = target
        return target

    if run:
        atexit.register(run_playbooks)

    return _target_deco if _target is None else _target_deco(_target)


def run_playbooks():
    """Execute playbooks, or prompt for one."""
    default_playbook = _DEFAULT_PLAYBOOK
    if len(_ALL_PLAYBOOKS) == 1 and not default_playbook:
        default_playbook = next(iter(_ALL_PLAYBOOKS))

    parser = argparse.ArgumentParser(
        description="Data Playbook v{}. Playbooks for tabular data.".format(VERSION)
    )
    parser.add_argument(
        "playbook",
        type=str,
        nargs="?",
        default=default_playbook,
        help=f"The playbook function name: {', '.join(_ALL_PLAYBOOKS)}",
    )
    parser.add_argument("-v", action="count", help="Debug level")
    parser.add_argument("--all", action="store_true", help="Load all tasks")
    args = parser.parse_args()

    setup_logger()

    if args.all:
        import dataplaybook.tasks.all  # noqa pylint: disable=unused-import,import-outside-toplevel

    if args.v > 2:
        print_tasks()

    retval = _ALL_PLAYBOOKS[args.playbook]()

    ic(ENV)

    sys.exit(retval)
