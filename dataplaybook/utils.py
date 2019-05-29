"""DataEnvironment class."""
import logging
import sys
from configparser import ConfigParser
from contextlib import contextmanager
from os import getenv
from pathlib import Path
from timeit import default_timer
from traceback import extract_tb
from typing import Any, Dict, List

from dataplaybook.config_validation import util_slugify
from dataplaybook.const import PlaybookError


class DataVars(dict):
    """DataVars supports key access to variables."""
    def __init__(self):
        """Read .env."""
        dict.__init__(self)

    def __getattr__(self, key):
        if key == 'env' and key not in self:
            dict.__setitem__(self, key, DataEnv())
        return self.get(key)

    def __setattr__(self, key, val):
        self[key] = val

    def __setitem__(self, key, val):
        """Ensure key is slug."""
        if key == 'env':
            raise PlaybookError("var.env is read-only")
        if key != util_slugify(key):
            raise PlaybookError(
                f"Invalid variable name '{key}' use '{util_slugify(key)}")
        dict.__setitem__(self, key, val)

    def as_table(self) -> List[Dict[str, Any]]:
        """Return as a table."""
        return [{'name': k, 'value': v} for k, v in self.items()]


class DataEnv(dict):
    """DataEnv."""
    def __init__(self):
        """Read .env."""
        dict.__init__(self)
        try:
            self._load(Path('.env').read_text())
        except FileNotFoundError:
            pass

    def _load(self, text: str):
        conf_str = '[env]\n' + text
        config = ConfigParser()
        config.read_string(conf_str)
        for key in config['env']:
            self[key] = config['env'][key]

    def __getitem__(self, key: str):
        res = self.get(key, None)
        if res is None:
            res = getenv(key, None)
            if res is None:
                raise PlaybookError(
                    f"Could not resolve '{key}' from .env or environment")
            self[key] = res
        return self.get(key)

    def __getattr__(self, key: str):
        return self[key]


class DataEnvironment(dict):
    """DataEnvironment supports key access and variables."""
    def __init__(self):
        dict.__setattr__(self, '_var', DataVars())
        dict.__setitem__(self, 'var', self._var)
        super().__init__()

    @property
    def var(self) -> Dict[str, Any]:
        """Return variables class."""
        return self._var

    def __getattr__(self, key: str) -> Any:
        return self[key]

    def __setattr__(self, key: str, val: Any):
        raise Exception(f'use [{key}]')

    def __getitem__(self, key: str):
        if key == 'var':
            return self._var.as_table()
        return dict.__getitem__(self, key)

    def __setitem__(self, key: str, val: Any):
        if key == 'var':
            raise Exception("Cannot set vaiables directly. Use .var.")
        dict.__setitem__(self, key, val)


def get_logger(logger=None):
    """Get a logger."""
    return (logger if isinstance(logger, logging.Logger)
            else logging.getLogger(logger or 'dataplaybook'))


def set_logger_level(level, module=None):
    """Set the log level."""
    def _level(level=None):
        try:
            return (getattr(logging, level.upper())
                    if isinstance(level, str) else level)
        except AttributeError:
            return logging.DEBUG if level else logging.INFO

    if isinstance(level, dict):
        assert module is None, 'module not supported when setting dict'
        for logr, lvl in level.items():
            logging.getLogger(logr).setLevel(_level(lvl))
        return

    level = _level(level)
    if module:
        get_logger(module).setLevel(level)

    for mod in ('dataplaybook.playbook',
                'dataplaybook.config_validation',
                ):
        get_logger(mod).setLevel(level)


def setup_logger():
    """Configure the color log handler."""
    logging.basicConfig(level=logging.DEBUG)
    # fmt = ("%(asctime)s %(levelname)s (%(threadName)s) "
    #        "[%(name)s] %(message)s")
    fmt = ("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    colorfmt = "%(log_color)s{}%(reset)s".format(fmt)
    datefmt = "%H:%M:%S"

    try:
        from colorlog import ColoredFormatter
        logging.getLogger().handlers[0].setFormatter(ColoredFormatter(
            colorfmt,
            datefmt=datefmt,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green,bold',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red',
            }
        ))
    except ImportError:
        pass


def print_exception(task_name=None, mod_name=None, logger='dataplaybook'):
    """Print last exception."""
    _, exc, traceback = sys.exc_info()
    tb_all = extract_tb(traceback)

    if mod_name:
        mod_name = mod_name.replace('.', '/')
        tb_show = list((fs for fs in tb_all
                        if fs.filename and mod_name in fs.filename))
        if tb_show:
            tb_all = tb_show

    if task_name:
        res = ["Exception in task {}: {}: {}".format(
            task_name, exc.__class__.__name__, exc)]
    else:
        res = ["Exception {}: {}".format(
            exc.__class__.__name__, exc)]

    for frame in tb_all:
        res.append(" File {} line {} in method {}".format(
            frame.filename, frame.lineno, frame.name))

    get_logger(logger).error(',\n '.join(res))


@contextmanager
def time_it(name=None, delta=2, logger=None):
    """Context manager to time execution and report if too high."""
    t_start = default_timer()
    yield
    total = default_timer() - t_start
    if total > delta:
        get_logger(logger).warning(
            "Execution time for %s: %.2fs", name, total)
    elif total > delta/2:
        get_logger(logger).debug(
            "Execution time for %s: %.2fs", name, total)
