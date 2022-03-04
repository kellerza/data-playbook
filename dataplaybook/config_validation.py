"""Data validation helpers for voluptuous."""
import logging
import os
from typing import Any, Callable, Sequence, TypeVar, Union

import voluptuous as vol

from dataplaybook.utils import slugify as util_slugify

# typing typevar
T = TypeVar("T")  # pylint: disable=invalid-name
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)


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


def isfile(value: Any) -> str:
    """Validate that the value is an existing file."""
    if value is None:
        raise vol.Invalid("None is not file")
    file_in = os.path.expanduser(str(value))

    if not os.path.isfile(file_in):
        raise vol.Invalid("not a file")
    if not os.access(file_in, os.R_OK):
        raise vol.Invalid("file not readable")
    return file_in


def slug(value: str) -> str:
    """Validate value is a valid slug."""
    if value is None:
        raise vol.Invalid("Slug should not be None")
    value = str(value)
    slg = util_slugify(value)
    if value == slg:
        return value
    raise vol.Invalid(f"invalid slug {value} (try {slg})")


def ensure_list_csv(value: Any) -> Sequence:
    """Ensure that input is a list or make one from comma-separated string."""
    if isinstance(value, str):
        return [member.strip() for member in value.split(",")]
    return ensure_list(value)


def ensure_list(value: Union[T, Sequence[T], None]) -> Sequence[T]:
    """Wrap value in list if it is not one."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]  # typing: ignore


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
