"""DataEnvironment class."""
from configparser import ConfigParser
from contextlib import contextmanager
import logging
from os import getenv
from pathlib import Path
import sys
from timeit import default_timer
from traceback import format_exception
from importlib import import_module
from typing import Any, Dict, List, Sequence
from functools import wraps

from icecream import ic

from dataplaybook.config_validation import util_slugify


_LOGGER = logging.getLogger(__name__)

# Cop of const...
Table = List[Dict[str, Any]]


class PlaybookError(Exception):
    """Playbook Exception. These typically have warnings and can be ignored."""


class DataVars(dict):
    """DataVars supports key access to variables."""

    def __init__(self):
        """Read .env."""
        dict.__init__(self)

    def __getattr__(self, key):
        if key == "env" and key not in self:
            dict.__setitem__(self, key, DataEnv())
        return self.get(key)

    def __setattr__(self, key, val):
        self[key] = val

    def __setitem__(self, key, val):
        """Ensure key is slug."""
        if key == "env":
            raise PlaybookError("var.env is read-only")
        if key != util_slugify(key):
            raise PlaybookError(
                f"Invalid variable name '{key}' use '{util_slugify(key)}"
            )
        dict.__setitem__(self, key, val)

    def as_table(self) -> List[Dict[str, Any]]:
        """Return as a table."""
        return [{"name": k, "value": v} for k, v in self.items()]


class DataEnv(dict):
    """DataEnv."""

    def __init__(self):
        """Read .env."""
        dict.__init__(self)
        try:
            self._load(Path(".env").read_text())
        except FileNotFoundError:
            pass

    def _load(self, text: str):
        conf_str = "[env]\n" + text
        config = ConfigParser()
        config.read_string(conf_str)
        for key in config["env"]:
            self[key] = config["env"][key]

    def __getitem__(self, key: str):
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

    def __getattr__(self, key: str):
        return self[key]


class DataEnvironment(dict):
    """DataEnvironment supports key access and variables."""

    def __init__(self):
        dict.__setattr__(self, "_var", DataVars())
        dict.__setitem__(self, "var", self._var)
        super().__init__()

    @property
    def var(self) -> Dict[str, Any]:
        """Return variables class."""
        return self._var

    def __getattr__(self, key: str) -> Any:
        return self[key]

    def __setattr__(self, key: str, val: Any):
        raise Exception(f"use [{key}]")

    def __getitem__(self, key: str):
        if key == "var":
            return self._var.as_table()
        return dict.__getitem__(self, key)

    def __setitem__(self, key: str, val: Any):
        if key == "var":
            raise Exception("Cannot set vaiables directly. Use .var.")
        else:
            raise Exception("Cannot set vaiables directly. Use set")

    def set(self, key: str, val: Any) -> Any:
        _LOGGER.debug("%s = %.50s", key, val)
        if isinstance(self, DataEnvironment):
            if isinstance(val, list):
                dict.__setitem__(self, key, val)
            else:
                self._var[key] = val
        else:
            self[key] = val
        return val

    def get(self, *table_names: str) -> Sequence[Table]:
        """Return a list of Tables."""
        return [self[n] for n in table_names if n in self]


def get_logger(logger=None):
    """Get a logger."""
    return (
        logger
        if isinstance(logger, logging.Logger)
        else logging.getLogger(logger or "dataplaybook")
    )


def set_logger_level(level, module=None):
    """Set the log level."""

    def _level(level=None):
        try:
            return getattr(logging, level.upper()) if isinstance(level, str) else level
        except AttributeError:
            return logging.DEBUG if level else logging.INFO

    if isinstance(level, dict):
        assert module is None, "module not supported when setting dict"
        for logr, lvl in level.items():
            logging.getLogger(logr).setLevel(_level(lvl))
        return

    level = _level(level)
    if module:
        get_logger(module).setLevel(level)

    for mod in ("dataplaybook.playbook", "dataplaybook.config_validation"):
        get_logger(mod).setLevel(level)


def setup_logger():
    """Configure the color log handler."""
    logging.basicConfig(level=logging.DEBUG)
    # fmt = ("%(asctime)s %(levelname)s (%(threadName)s) "
    #        "[%(name)s] %(message)s")
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message).500s"
    colorfmt = "%(log_color)s{}%(reset)s".format(fmt)
    datefmt = "%H:%M:%S"

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


def log_filter(record):
    """Trim log messages.

    https://relaxdiego.com/2014/07/logging-in-python.html
    """
    if any(len(str(arg)) > 100 for arg in record.args):
        ic(record, record.args)
        res = []
        for arg in record.args:
            if len(str(arg)) < 100:
                res.append(arg)
                continue
            idx = len(res)
            res.append(f"{str(arg)[:100]}...q...len={len(arg)}")
            ic(record.args[idx], type(record.args[idx]))
        record.args = tuple(res)
        return record

    return True


def print_exception(task_name=None, mod_name=None, logger="dataplaybook"):
    """Print last exception."""
    exc_type, exc_value, traceback = sys.exc_info()
    res = format_exception(exc_type, exc_value, traceback)
    if mod_name:
        res[0] += f" Module: {mod_name}"
    if task_name:
        res[0] += f" Task: {task_name}"
    get_logger(logger).error("".join(res))

    #     _, exc, traceback = sys.exc_info()
    #     tb_all = extract_tb(traceback)

    #     if mod_name:
    #         mod_name = mod_name.replace(".", "/")
    #         tb_show = list((fs for fs in tb_all if fs.filename and mod_name in fs.filename))
    #         if tb_show:
    #             tb_all = tb_show

    #     if task_name:
    #         res = [
    #             "Exception in task {}: {}: {}".format(
    #                 task_name, exc.__class__.__name__, exc
    #             )
    #         ]
    #     else:
    #         res = ["Exception {}: {}".format(exc.__class__.__name__, exc)]

    #     res.insert(0, "Tracebcak (most recent call last)")

    #     for frame in tb_all:
    #         res.insert(
    #             0,
    #             " File {} line {} in method {}".format(
    #                 frame.filename, frame.lineno, frame.name
    #             ),
    #         )
    # get_logger(logger).error(",\n ".join(res))


@contextmanager
def time_it(name=None, delta=2, logger=None):
    """Context manager to time execution and report if too high."""
    t_start = default_timer()
    yield
    total = default_timer() - t_start
    if total > delta:
        get_logger(logger).warning("Execution time for %s: %.2fs", name, total)
    elif total > delta / 2:
        get_logger(logger).debug("Execution time for %s: %.2fs", name, total)


def complete_import(mod_name):
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

    path = Path(mod_name + ".py").resolve(strict=True)
    mod_name = path.stem

    sys.path.insert(0, str(path.parent))
    try:
        mod_obj = import_module(mod_name)
        return mod_obj
    finally:
        if sys.path[0] == path.parent:
            sys.path.pop(0)


def doublewrap(f):
    """
    a decorator decorator, allowing the decorator to be used as:
    @decorator(with, arguments, and=kwargs)
    or
    @decorator
    """

    @wraps(f)
    def new_dec(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # actual decorated function
            return f(args[0])
        else:
            # decorator arguments
            return lambda realf: f(realf, *args, **kwargs)

    return new_dec
