"""DataEnvironment class."""

import logging
import re
import sys
import typing as t
from collections import abc
from contextlib import contextmanager
from functools import wraps
from importlib import import_module
from pathlib import Path
from timeit import default_timer
from types import ModuleType

from .ensure import (  # noqa: F401
    ensure_bool,
    ensure_bool_str,
    ensure_datetime,
    ensure_instant,
    ensure_list,
    ensure_set,
    ensure_string,
)
from .lists import append_unique, extract_pattern, strip, unique  # noqa: F401
from .logger import get_logger

_LOGGER = logging.getLogger(__name__)
RE_SLUGIFY = re.compile(r"[^a-z0-9_]+")


class PlaybookError(Exception):
    """Playbook Exception. These typically have warnings and can be ignored."""


T = t.TypeVar("T")


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
) -> abc.Iterator[None]:
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


PDW = t.ParamSpec("PDW")  # used for doublewrap
RT = t.TypeVar("RT", bound=t.Callable)


def doublewrap(
    fun: t.Callable[t.Concatenate[t.Callable, PDW], t.Callable[PDW, t.Any]],
) -> t.Callable[PDW, t.Any]:
    """Decorate the decorators.

    Allow the decorator to be used as:
    @decorator(with, arguments, and=kwargs)
    or
    @decorator
    """

    @wraps(fun)
    def new_dec(*args: PDW.args, **kwargs: PDW.kwargs) -> t.Callable[PDW, t.Any]:
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # called as @decorator
            return fun(args[0])  # type: ignore[call-arg]

        # called as @decorator(*args, **kwargs)
        # def new_dec2(realf: PDW) -> t.Any:
        #     return fun(realf, *args, **kwargs)

        # return new_dec2
        return lambda realf: fun(realf, *args, **kwargs)  # type:ignore[return-value]

    return new_dec


class AttrKeyError(KeyError):
    """Key not found in dict."""


class AttrDict(dict):
    """Simple recursive read-only attribute access (i.e. Munch)."""

    def __getattr__(self, key: str) -> t.Any:
        """Get attribute."""
        try:
            value = self[key]
        except KeyError as err:
            raise AttrKeyError(f"Key '{key}' not found in dict {self}") from err
        return AttrDict(value) if isinstance(value, dict) else value

    def __setattr__(self, key: str, value: t.Any) -> None:
        """Set attribute."""
        raise OSError("Read only")

    def __repr__(self) -> str:
        """Represent."""
        lst = [
            ("{}='{}'" if isinstance(v, str) else "{}={}").format(k, v)
            for k, v in self.items()
        ]
        return "(" + ", ".join(lst) + ")"
