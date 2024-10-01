"""DataEnvironment class."""

import logging
import re
import sys
import typing
from contextlib import contextmanager
from functools import wraps
from importlib import import_module
from inspect import isgenerator
from pathlib import Path
from timeit import default_timer
from types import ModuleType
from typing import Any

from typing_extensions import Concatenate, ParamSpec

from dataplaybook.utils.logger import get_logger

_LOGGER = logging.getLogger(__name__)
RE_SLUGIFY = re.compile(r"[^a-z0-9_]+")


class PlaybookError(Exception):
    """Playbook Exception. These typically have warnings and can be ignored."""


T = typing.TypeVar("T")


def ensure_list(
    value: T | list[T] | tuple[T] | typing.Generator[T, None, None],
) -> list[T]:
    """Wrap value in list if it is not one."""
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    if isgenerator(value):
        return list(value)
    return [value]  # type: ignore


def ensure_list_csv(value: Any) -> typing.Sequence:
    """Ensure that input is a list or make one from comma-separated string."""
    if isinstance(value, str):
        return [member.strip() for member in value.split(",")]
    return ensure_list(value)


def slugify(text: str) -> str:
    """Slugify a given text."""
    # text = normalize('NFKD', text)
    text = text.lower()
    text = text.replace(" ", "_")
    # text = text.translate(TBL_SLUGIFY)
    text = RE_SLUGIFY.sub("", text)

    return text


@contextmanager
def time_it(
    name: str | None = None, delta: int = 2, logger: logging.Logger | None = None
) -> typing.Iterator[None]:
    """Context manager to time execution and report if too high."""
    t_start = default_timer()
    yield
    total = default_timer() - t_start
    if total > delta:
        get_logger(logger).warning("Execution time for %s: %.2fs", name, total)
    elif total > delta / 2:
        get_logger(logger).debug("Execution time for %s: %.2fs", name, total)


def local_import_module(mod_name: str) -> ModuleType:
    """import_module that searches local path."""
    path = Path(mod_name + ".py").resolve()
    mod_name = path.stem
    pstr = str(path.parent)
    sys.path.insert(0, pstr)
    try:
        mod_obj = import_module(mod_name)
        return mod_obj
    finally:
        if sys.path[0] == pstr:
            sys.path.pop(0)


PDW = ParamSpec("PDW")  # used for doublewrap


def doublewrap(
    fun: typing.Callable[Concatenate[typing.Callable, PDW], typing.Callable[PDW, Any]],
) -> typing.Callable[PDW, Any]:
    """Decorate the decorators.

    Allow the decorator to be used as:
    @decorator(with, arguments, and=kwargs)
    or
    @decorator
    """

    @wraps(fun)
    def new_dec(*args: Any, **kwargs: Any) -> typing.Callable[PDW, Any]:
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # called as @decorator
            return fun(args[0])

        # called as @decorator(*args, **kwargs)
        # def new_dec2(realf: PDW) -> Any:
        #     return fun(realf, *args, **kwargs)

        # return new_dec2
        return lambda realf: fun(realf, *args, **kwargs)  # type:ignore

    return new_dec


class AttrKeyError(KeyError):
    """Key not found in dict."""

    pass


class AttrDict(dict):
    """Simple recursive read-only attribute access (i.e. Munch)."""

    def __getattr__(self, key: str) -> Any:
        """Get attribute."""
        try:
            value = self[key]
        except KeyError as err:
            raise AttrKeyError(f"Key '{key}' not found in dict {self}") from err
        return AttrDict(value) if isinstance(value, dict) else value

    def __setattr__(self, key: str, value: Any) -> None:
        """Set attribute."""
        raise IOError("Read only")

    def __repr__(self) -> str:
        """Represent."""
        lst = [
            ("{}='{}'" if isinstance(v, str) else "{}={}").format(k, v)
            for k, v in self.items()
        ]
        return "(" + ", ".join(lst) + ")"
