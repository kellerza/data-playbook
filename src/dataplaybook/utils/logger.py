"""Logger functions."""

import logging
from typing import Any


def get_logger(logger: str | logging.Logger | None = None) -> logging.Logger:
    """Get a logger."""
    return (
        logger
        if isinstance(logger, logging.Logger)
        else logging.getLogger(logger or "dataplaybook")
    )


def set_logger_level(level: Any, module: logging.Logger | None = None) -> None:
    """Set the log level."""

    def _level(level: Any = None) -> int:
        try:
            return int(
                getattr(logging, level.upper()) if isinstance(level, str) else level
            )
        except AttributeError:
            return logging.DEBUG if level else logging.INFO

    if isinstance(level, dict):
        if module:
            raise RuntimeError(f"module should be None when setting dict, got {module}")
        for logr, lvl in level.items():
            logging.getLogger(logr).setLevel(_level(lvl))
        return

    level = _level(level)
    if module:
        get_logger(module).setLevel(level)

    for mod in "dataplaybook.playbook":  # , "dataplaybook.config_validation"):
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
        from colorlog import ColoredFormatter

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
