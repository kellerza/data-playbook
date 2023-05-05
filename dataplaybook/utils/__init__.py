"""DataEnvironment class."""
import logging
import re
import sys
from contextlib import contextmanager
from functools import wraps
from importlib import import_module
from pathlib import Path
from timeit import default_timer
from types import ModuleType
from typing import Any, Callable, Iterator, Optional, Sequence, TypeVar, Union

from typing_extensions import Concatenate, ParamSpec

from dataplaybook.utils.logger import get_logger

_LOGGER = logging.getLogger(__name__)
RE_SLUGIFY = re.compile(r"[^a-z0-9_]+")
Table = list[dict[str, Any]]


class PlaybookError(Exception):
    """Playbook Exception. These typically have warnings and can be ignored."""


T = TypeVar("T")


def ensure_list(value: Union[T, Sequence[T], None]) -> Sequence[T]:
    """Wrap value in list if it is not one."""
    if value is None:
        return []
    return value if isinstance(value, (list, tuple)) else [value]  # type: ignore


def ensure_list_csv(value: Any) -> Sequence:
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
    name: Optional[str] = None, delta: int = 2, logger: Optional[logging.Logger] = None
) -> Iterator[None]:
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
    try:
        mod_obj = import_module(mod_name)
        return mod_obj
    except ModuleNotFoundError as err:
        if err.name != mod_name:
            _LOGGER.error(
                "No module named '%s' found while trying to import '%s'",
                err.name,
                mod_name,
            )
            raise
        pass

    path = Path(mod_name + ".py").resolve()
    if not path.exists():
        raise FileNotFoundError(f"Cannot find {path} CWD={Path.cwd()}")
    mod_name = path.stem

    sys.path.insert(0, str(path.parent))
    try:
        mod_obj = import_module(mod_name)
        return mod_obj
    finally:
        if sys.path[0] == path.parent:
            sys.path.pop(0)


PDW = ParamSpec("PDW")  # used for doublewrap


def doublewrap(
    fun: Callable[Concatenate[Callable, PDW], Callable[PDW, Any]]
) -> Callable[PDW, Any]:
    """Decorate the decorators.

    Allow the decorator to be used as:
    @decorator(with, arguments, and=kwargs)
    or
    @decorator
    """

    @wraps(fun)
    def new_dec(*args: Any, **kwargs: Any) -> Callable:
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # called as @decorator
            return fun(args[0])
        # called as @decorator(*args, **kwargs)
        return lambda realf: fun(realf, *args, **kwargs)

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
