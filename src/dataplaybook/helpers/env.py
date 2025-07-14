"""Dataenvironment class."""

from __future__ import annotations
import logging
import typing as t
from collections import abc
from configparser import ConfigParser
from inspect import isgenerator
from os import getenv
from pathlib import Path
from typing import Any

from dataplaybook.utils import slugify

_LOGGER = logging.getLogger(__name__)
# Table = list[dict[str, Any]]

if t.TYPE_CHECKING:
    from dataplaybook.const import RowData


class DataVars(dict):
    """DataVars supports key access to variables."""

    def __init__(self) -> None:
        """Read .env."""
        dict.__init__(self)

    def __getattr__(self, key: str) -> Any:
        """Get attribute."""
        if key == "env" and key not in self:
            dict.__setitem__(self, key, _DataEnv())
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

    def as_table(self) -> list[dict[str, Any]]:
        """Return as a table."""
        return [{"name": k, "value": v} for k, v in self.items()]


class _DataEnv(dict):
    """DataEnv."""

    def __init__(self) -> None:
        """Read .env."""
        dict.__init__(self)
        try:
            self._load(Path(".env").read_text(encoding="utf-8"))
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


class DataEnvironment(dict[str, list[dict[str, Any]]]):
    """DataEnvironment supports key access and variables."""

    _var: DataVars

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Init."""
        dict.__setattr__(self, "_var", DataVars())
        dict.__setitem__(self, "var", self._var)  # type:ignore[misc]
        super().__init__(*args, **kwargs)

    @property
    def var(self) -> DataVars:
        """Return variables class."""
        return self._var

    def __getattr__(self, key: str) -> Any:
        """Get attribute."""
        return self[key]

    def __setattr__(self, key: str, val: Any) -> None:
        """Set attribute."""
        raise SyntaxError(f"use [{key}]")

    def __getitem__(self, key: str) -> Any:
        """Get item."""
        if key == "var":
            return self._var.as_table()
        return dict.__getitem__(self, key)

    def __setitem__(self, key: str, val: Any) -> None:
        """Set item."""
        if key == "var":
            raise SyntaxError("Cannot set variables directly. Use .var.")
        if isinstance(val, list):
            dict.__setitem__(self, key, val)
            _LOGGER.debug("tables[%s] = %s", key, val)
            return
        if isgenerator(val):
            dict.__setitem__(self, key, list(val))
            _LOGGER.debug("tables[%s] = list(...)", key)
            return
        self._var[key] = val
        _LOGGER.debug("tables.var[%s] = %s", key, val)

    def _check_keys(self, *table_names: str) -> abc.Sequence[str]:
        res = []
        for name in table_names:
            if name in self:
                if isinstance(self[name], list):
                    res.append(name)
                else:
                    _LOGGER.warning("Table %s is not a list: %s", name, self[name])
            else:
                _LOGGER.warning("Table %s does not exist", name)
        if not table_names:
            res = [k for k, v in self.items() if isinstance(v, list)]
        return res

    def as_dict(self, *table_names: str) -> dict[str, list[RowData]]:
        """Return an ordered dict."""
        keys = self._check_keys(*table_names)
        res = {}
        for key in keys:
            res[key] = self[key]
        return res

    def as_list(self, *table_names: str) -> abc.Sequence[list[RowData]]:
        """Return a list of Tables."""
        keys = self._check_keys(*table_names)
        return [self[k] for k in keys]
