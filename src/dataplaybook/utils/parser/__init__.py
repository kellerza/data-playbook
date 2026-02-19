"""Parse & convert."""

import logging
from collections import abc
from typing import Any, Literal, Self, TypeVar, cast, get_origin

from cattrs._compat import adapted_fields
from cattrs.errors import ClassValidationError, ForbiddenExtraKeysError
from cattrs.gen import make_dict_structure_fn
from icecream import ic
from typing_extensions import deprecated  # In Python 3.13 it moves to warnings

from ..ensure import ensure_list
from . import parse
from .convert import (
    CONVERT,
    Converter,
    get_converter,
    transform_error,
)

_LOG = logging.getLogger(__name__)
T = TypeVar("T")
# DT = TypeVar("DT", bound=dict[str, Any] | abc.Mapping[str, Any])

type RowMapping = abc.Mapping[str, Any] | dict[str, Any]


class BaseClass:
    """Base class for cattrs conversions."""

    def asdict(
        self,
        only_keys: abc.Iterable[str] | None = None,
        exclude_keys: abc.Iterable[str] | None = None,
        omit_if_default: bool = True,
    ) -> dict[str, Any]:
        """Return class as a dictionary. Unstructure."""
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
        cls,
        data: abc.Mapping[str, Any],
        *,
        lenient: bool = False,
    ) -> Self:
        """Convert a dictionary to class instance."""
        cvt = cast(Converter, getattr(cls, "converter", CONVERT))
        try:
            return cvt.structure(data, cls)
        except (ClassValidationError, ForbiddenExtraKeysError) as err:
            msg = "; ".join(transform_error(err))
            _LOG.error(msg)
            cls.log_item(data)
            if not (lenient and "extra fields" in msg):
                raise

        _LOG.debug("allow extra!")
        cvt = get_converter(forbid_extra_keys=False)
        try:
            return cvt.structure(data, cls)
        except (ClassValidationError, ForbiddenExtraKeysError) as err:
            msg = "; ".join(transform_error(err))
            _LOG.error(msg)
            raise

    @classmethod
    def structure_list(
        cls,
        data: abc.Iterator[RowMapping] | list[RowMapping],
        log: int = 0,
        lenient: bool = False,
    ) -> list[Self]:
        """Convert list of dictionaries to list of class instances."""
        return list(cls.structure_iter(data, log=log, lenient=lenient))

    @classmethod
    def structure_iter(
        cls,
        iteratr: abc.Iterable[RowMapping],
        *,
        log: int = 0,
        lenient: bool = False,
    ) -> abc.Generator[Self, None]:
        """Structure a generator/iterator."""
        for row in iteratr:
            res = cls.structure(row, lenient=lenient)
            if log > 0:
                log = cls.log_item(res, log_n=log)
            yield res

    @classmethod
    def structure_iter_orig(
        cls,
        iteratr: abc.Iterable[RowMapping],
        *,
        include_original: Literal[True],
        log: int = 0,
        lenient: bool = False,
    ) -> abc.Generator[tuple[RowMapping, Self], None]:
        """Structure a generator/iterator. Include original row in the output."""
        for row in iteratr:
            res = cls.structure(row, lenient=lenient)
            if log > 0:
                log = cls.log_item(res, log_n=log)
            yield row, res

    @classmethod
    async def async_structure(
        cls,
        iteratr: abc.AsyncIterable[RowMapping],
        *,
        log: int = 0,
        lenient: bool = False,
    ) -> abc.AsyncGenerator[Self, None]:
        """Structure a async generator."""
        async for row in iteratr:
            res = cls.structure(row, lenient=lenient)
            if log > 0:
                log = cls.log_item(res, log_n=log)
            yield res

    @classmethod
    async def async_structure_orig(
        cls,
        iteratr: abc.AsyncIterable[RowMapping],
        *,
        log: int = 0,
        lenient: bool = False,
    ) -> abc.AsyncGenerator[tuple[RowMapping, Self], None]:
        """Structure an async generator. Include original row in the output."""
        async for row in iteratr:
            res = cls.structure(row, lenient=lenient)
            if log > 0:
                log = cls.log_item(res, log_n=log)
            yield row, res

    @classmethod
    def log_item(cls, data: Any, *, log_n: int = 1) -> int:
        """Log an item and decrement by 1."""
        if log_n <= 0:
            return 0
        ic(data)
        return log_n - 1


C = TypeVar("C", bound=BaseClass)


@deprecated("Use BaseClass.async_structure_orig instead")
async def async_structure(
    iteratr: abc.AsyncGenerator[RowMapping, None] | abc.AsyncIterator[RowMapping],
    cls: type[C],
    *,
    log: int = 0,
    lenient: bool = False,
) -> abc.AsyncGenerator[tuple[RowMapping, C], None]:
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
        try:
            struct = make_dict_structure_fn(cls, converter_arg, _cattrs_use_alias=True)  # type: ignore[var-annotated,arg-type]
        except Exception:
            struct = None

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

            nonlocal struct
            if struct is None:
                # try:
                struct = make_dict_structure_fn(
                    cls,  # type: ignore[var-annotated,arg-type]
                    converter_arg,
                    _cattrs_use_alias=True,
                )
                # except TypeError:
                #     the_cl = cls._evaluate(globals(), locals(), frozenset())
                #     struct = make_dict_structure_fn(
                #         cl, converter_arg, _cattrs_use_alias=True
                #     )

            return struct(d, cl)

        converter_arg.register_structure_hook(cls, structure)

        return cls

    return decorator


@deprecated("Use BaseClass.structure instead")
def structure1(data: Any, cls: type[T]) -> T:
    """Structure simple values."""
    try:
        return CONVERT.structure(data, cls)
    except ClassValidationError as err:
        raise ValueError("; ".join(transform_error(err)))  # noqa: B904


@deprecated("Use BaseClass.structure_list instead")
def structure_list(
    iteratr: abc.Sequence[dict],
    cls: type[C],
    *,
    log: int = 0,
    lenient: bool = False,
) -> abc.Generator[tuple[abc.Mapping[str, Any], C], None, None]:
    """Structure a list."""
    for row in iteratr:
        res = _structure1(CONVERT, row, cls, allow_ignore_extra=lenient)

        if log > 0:
            log = log - 1
            ic(row, res)

        yield row, res


@deprecated("Use BaseClass.structure instead")
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
