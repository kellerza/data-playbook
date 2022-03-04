"""DataEnvironment class."""
import logging
import re
import sys
from configparser import ConfigParser
from contextlib import contextmanager
from functools import wraps
from importlib import import_module
from os import getenv
from pathlib import Path
from timeit import default_timer
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Sequence

_LOGGER = logging.getLogger(__name__)
RE_SLUGIFY = re.compile(r"[^a-z0-9_]+")
Table = List[Dict[str, Any]]


def slugify(text: str) -> str:
    """Slugify a given text."""
    # text = normalize('NFKD', text)
    text = text.lower()
    text = text.replace(" ", "_")
    # text = text.translate(TBL_SLUGIFY)
    text = RE_SLUGIFY.sub("", text)

    return text


class PlaybookError(Exception):
    """Playbook Exception. These typically have warnings and can be ignored."""


class DataVars(dict):
    """DataVars supports key access to variables."""

    def __init__(self) -> None:
        """Read .env."""
        dict.__init__(self)

    def __getattr__(self, key: str) -> Any:
        """Get attribute."""
        if key == "env" and key not in self:
            dict.__setitem__(self, key, DataEnv())
        return self.get(key)

    def __setattr__(self, key: str, val: Any) -> None:
        """Set attribute."""
        self[key] = val

    def __setitem__(self, key: str, val: Any) -> None:
        """Ensure key is slug."""
        if key == "env":
            raise KeyError("var.env is read-only")
        if key != slugify(key):
            raise KeyError(f"Invalid variable name '{key}' use '{slugify(key)}")
        dict.__setitem__(self, key, val)

    def as_table(self) -> List[Dict[str, Any]]:
        """Return as a table."""
        return [{"name": k, "value": v} for k, v in self.items()]


class DataEnv(dict):
    """DataEnv."""

    def __init__(self) -> None:
        """Read .env."""
        dict.__init__(self)
        try:
            self._load(Path(".env").read_text(encoding="utf8"))
        except FileNotFoundError:
            pass

    def _load(self, text: str) -> None:
        """Load."""
        conf_str = "[env]\n" + text
        config = ConfigParser()
        config.read_string(conf_str)
        for key in config["env"]:
            self[key] = config["env"][key]

    def __getitem__(self, key: str) -> Any:
        """Get item."""
        res = self.get(key, None)
        if res is None:
            res = getenv(key, None)
            if res is None:
                _LOGGER.critical("Could not resolve '%s' from .env or environment", key)
                # raise PlaybookError(
                #     f"Could not resolve '{key}' from .env or environment"
                # )
                # return ""
            self[key] = res
        return self.get(key)

    def __getattr__(self, key: str) -> Any:
        """Get attribute."""
        return self[key]


class DataEnvironment(dict):
    """DataEnvironment supports key access and variables."""

    def __init__(self) -> None:
        """Init."""
        dict.__setattr__(self, "_var", DataVars())
        dict.__setitem__(self, "var", self._var)
        super().__init__()

    @property
    def var(self) -> DataVars:
        """Return variables class."""
        return self._var

    def __getattr__(self, key: str) -> Any:
        """Get attribute."""
        return self[key]

    def __setattr__(self, key: str, val: Any) -> None:
        """Set attribute."""
        raise Exception(f"use [{key}]")

    def __getitem__(self, key: str) -> Any:
        """Get item."""
        if key == "var":
            return self._var.as_table()
        return dict.__getitem__(self, key)

    def __setitem__(self, key: str, val: Any) -> None:
        """Set item."""
        if key == "var":
            raise Exception("Cannot set variables directly. Use .var.")
        if isinstance(val, list):
            dict.__setitem__(self, key, val)
            _LOGGER.debug("tables[%s] = %s", key, val)
        else:
            self._var[key] = val
            _LOGGER.debug("tables.var[%s] = %s", key, val)

    def _check_keys(self, *table_names: str) -> Sequence[str]:
        res = []
        for name in table_names:
            if name in self:
                if isinstance(self[name], list):
                    res.append(name)
                else:
                    _LOGGER.warning("Table {%s} is not a list: %s", name, self[name])
            else:
                _LOGGER.warning("Table {%s} does not exist", name)
        if not table_names:
            res = [k for k, v in self.items() if isinstance(v, list)]
        return res

    def as_dict(self, *table_names: str) -> Dict[str, Table]:
        """Return an ordered dict."""
        keys = self._check_keys(*table_names)
        res = {}
        for key in keys:
            res[key] = self[key]
        return res

    def as_list(self, *table_names: str) -> Sequence[Table]:
        """Return a list of Tables."""
        keys = self._check_keys(*table_names)
        return [self[k] for k in keys]


def get_logger(logger=None) -> logging.Logger:
    """Get a logger."""
    return (
        logger
        if isinstance(logger, logging.Logger)
        else logging.getLogger(logger or "dataplaybook")
    )


def set_logger_level(level, module=None) -> None:
    """Set the log level."""

    def _level(level=None) -> int:
        try:
            return getattr(logging, level.upper()) if isinstance(level, str) else level
        except AttributeError:
            return logging.DEBUG if level else logging.INFO

    if isinstance(level, dict):
        if module:
            raise Exception(f"module should be None when setting dict, got {module}")
        for logr, lvl in level.items():
            logging.getLogger(logr).setLevel(_level(lvl))
        return

    level = _level(level)
    if module:
        get_logger(module).setLevel(level)

    for mod in ("dataplaybook.playbook", "dataplaybook.config_validation"):
        get_logger(mod).setLevel(level)


def setup_logger() -> None:
    """Configure the color log handler."""
    logging.basicConfig(level=logging.DEBUG)
    # fmt = ("%(asctime)s %(levelname)s (%(threadName)s) "
    #        "[%(name)s] %(message)s")
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message).500s"
    colorfmt = f"%(log_color)s{fmt}%(reset)s"
    datefmt = "%H:%M:%S"

    logging.getLogger().handlers[0].addFilter(log_filter)

    try:
        from colorlog import ColoredFormatter  # pylint: disable=import-outside-toplevel

        logging.getLogger().handlers[0].setFormatter(
            ColoredFormatter(
                colorfmt,
                datefmt=datefmt,
                reset=True,
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green,bold",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red",
                },
            )
        )
    except ImportError:
        pass


def log_filter(record: Any) -> Any:
    """Trim log messages.

    https://relaxdiego.com/2014/07/logging-in-python.html
    """
    changed = False
    res = []
    for arg in record.args:
        sarg = str(arg)
        if len(sarg) < 150:
            res.append(arg)
            continue
        res.append(f"{sarg[:130]}...{sarg[-20:]} len={len(sarg)} type={type(arg)}")
        changed = True
    if changed:
        record.args = tuple(res)
        return record
    return True


@contextmanager
def time_it(
    name: Optional[str] = None, delta: int = 2, logger: logging.Logger = None
) -> None:
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


def doublewrap(fun: Callable) -> Callable:
    """Decorate the decorators.

    Allow the decorator to be used as:
    @decorator(with, arguments, and=kwargs)
    or
    @decorator
    """

    @wraps(fun)
    def new_dec(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # actual decorated function
            return fun(args[0])
        # decorator arguments
        return lambda realf: fun(realf, *args, **kwargs)

    return new_dec
