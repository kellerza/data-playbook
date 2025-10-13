"""Parse & convert."""

import logging
from collections import abc
from typing import Any, Self, TypeVar, get_origin

from cattrs._compat import adapted_fields
from cattrs.errors import ClassValidationError, ForbiddenExtraKeysError
from cattrs.gen import make_dict_structure_fn
from icecream import ic

from ..ensure import ensure_list
from . import parse
from .convert import (
    CONVERT,
    Converter,
    get_converter,
    transform_error,
)

_LOG = logging.getLogger(__name__)


class BaseClass:
    """Base class for cattrs conversions."""

    def asdict(
        self,
        only_keys: abc.Iterable[str] | None = None,
        exclude_keys: abc.Iterable[str] | None = None,
        omit_if_default: bool = True,
    ) -> dict[str, Any]:
        """Return class as a dictionary."""
        cvt = get_converter(omit_if_default=omit_if_default)
        res = cvt.unstructure(self)
        if only_keys:
            assert exclude_keys is None, "Cannot have both only_keys and exclude_keys"
            return {k: v for k, v in res.items() if k in only_keys}
        if exclude_keys:
            return {k: v for k, v in res.items() if k not in exclude_keys}
        return res

    @classmethod
    def structure(
        cls, data: abc.Mapping[str, Any], allow_ignore_extra: bool = False
    ) -> Self:
        """Convert dictionary to class instance."""
        return _structure1(CONVERT, data, cls, allow_ignore_extra=allow_ignore_extra)

    @classmethod
    def structure_list(cls, data: abc.Sequence[abc.Mapping[str, Any]]) -> list[Self]:
        """Convert list of dictionaries to list of class instances."""
        return [_structure1(CONVERT, d, cls) for d in data]


C = TypeVar("C", bound=BaseClass)
T = TypeVar("T")
DT = TypeVar("DT", bound=dict[str, Any] | abc.Mapping[str, Any])


async def async_structure(
    iteratr: abc.AsyncGenerator[DT, None] | abc.AsyncIterator[DT],
    cls: type[C],
    *,
    log: int = 0,
    lenient: bool = False,
) -> abc.AsyncGenerator[tuple[abc.Mapping[str, Any], C], None]:
    """Structure a async generator."""
    async for row in iteratr:
        res = _structure1(CONVERT, row, cls, allow_ignore_extra=lenient)
        if log > 0:
            log = log - 1
            ic(row, res)

        yield row, res


def pre_process(
    converter_arg: Converter = CONVERT,
    *,
    unknown_field: str = "",
    parser: parse.Parser | None = None,
    start_unknown_fields: bool = False,
    debug: bool = False,
) -> abc.Callable[[T], T]:
    """Help rename/migrate field names."""

    def decorator(cls: T) -> T:
        struct = make_dict_structure_fn(cls, converter_arg, _cattrs_use_alias=True)  # type: ignore[var-annotated,arg-type]

        def unknown_field_hook(d: dict[str, Any]) -> None:
            """Move unknown fields to unknown_field."""
            if not unknown_field:
                return
            if not isinstance(d, dict):
                _LOG.warning(
                    "Cannot process unknown field for non-dict: %s %s", type(d), d
                )
                return
            fields = adapted_fields(get_origin(cls) or cls)  # type: ignore[arg-type]
            all_fields = {a.alias or a.name for a in fields}
            if debug:
                _LOG.debug(
                    "Available fields %s. Incoming keys: %s", all_fields, d.keys()
                )
            unk_fields = set(d.keys()) - all_fields
            if unk_fields:
                unk = d.get(unknown_field)
                if not isinstance(unk, dict):
                    d[unknown_field] = unk = {unknown_field: unk} if unk else {}
                # now unk is a dict, add
                for key in unk_fields:
                    unk[key] = _append(unk.get(key), d.pop(key))
                if debug:
                    _LOG.warning(
                        "Unknown fields %s moved to %s --> %s",
                        unk_fields,
                        unknown_field,
                        d.keys(),
                    )

        def structure(d: dict[str, Any], cl: Any) -> Any:
            if isinstance(d, cl):
                return d
            if start_unknown_fields:
                unknown_field_hook(d)
            if parser:
                parser(d, in_place=True)
            if not start_unknown_fields:
                unknown_field_hook(d)

            if debug:
                _LOG.debug("Structure: %s", d)

            return struct(d, cl)

        converter_arg.register_structure_hook(cls, structure)

        return cls

    return decorator


def structure1(data: Any, cls: type[T]) -> T:
    """Structure simple values."""
    try:
        return CONVERT.structure(data, cls)
    except ClassValidationError as err:
        raise ValueError("; ".join(transform_error(err)))  # noqa: B904


def structure_list(
    iteratr: abc.Sequence[dict],
    cls: type[C],
    *,
    log: int = 0,
    lenient: bool = False,
) -> abc.Generator[tuple[abc.Mapping[str, Any], C], None, None]:
    """Structure a async generator."""
    for row in iteratr:
        res = _structure1(CONVERT, row, cls, allow_ignore_extra=lenient)

        if log > 0:
            log = log - 1
            ic(row, res)

        yield row, res


def _structure1(
    cvt: Converter,
    data: abc.Mapping[str, Any],
    cls: type[C],
    *,
    allow_ignore_extra: bool = False,
) -> C:
    """Structure printing errors."""
    try:
        return cvt.structure(data, cls)

    except (ClassValidationError, ForbiddenExtraKeysError) as err:
        msg = "; ".join(transform_error(err))
        _LOG.error(msg)
        ic(msg, data)
        if allow_ignore_extra and "extra fields" in msg:
            _LOG.debug("allow extra!")
            cvt = get_converter(forbid_extra_keys=False)
            return _structure1(cvt, data, cls, allow_ignore_extra=False)
        raise


def _append(maybelist: Any, add: Any) -> Any:
    """Append value to the list."""
    if not add or maybelist == add:
        return maybelist
    if not maybelist:
        return add
    alist = ensure_list(maybelist)
    if add not in alist:
        alist.append(add)
    return alist
