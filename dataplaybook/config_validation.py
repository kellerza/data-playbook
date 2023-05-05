"""Data validation helpers for voluptuous."""
import logging
from typing import Any, Callable

import voluptuous as vol

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)


def endswith(parts: str) -> Callable[[Any], Any]:
    """Ensure a string ends with specified part."""

    def _check(_str: str) -> str:
        """Return the validator."""
        if _str.endswith(parts):
            return _str
        raise vol.Invalid(f"{_str} does not end with {parts}")

    return _check


def ensure_tables(value: Any) -> Any:
    """Ensure you have a dict of tables."""
    if not isinstance(value, dict):
        raise vol.Invalid("tables need to be a dict")
    for key, val in value.items():
        if key == "var":
            continue
        if not isinstance(val, list):
            raise vol.Invalid(
                f"tables need to contain lists {key} contains {type(val)}"
            )
    return value
