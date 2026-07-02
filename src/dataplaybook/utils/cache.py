"""Cache utils."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, cast

from whenever import Instant


@dataclass
class CacheDict[KT, RT]:
    """Cache values for a certain amount of minutes."""

    minutes: int = 10
    _cache: dict[KT, tuple[int, RT]] = field(default_factory=dict)
    _lasttick: int = 0

    def clear(self, *keys: KT | Callable) -> None:
        """Clear keys."""
        if not keys:
            self._cache.clear()
            return

        find_keys = tuple(key.__qualname__ if callable(key) else key for key in keys)
        cache_keys = list(self._cache.keys())

        for fk in find_keys:
            for ck in cache_keys:
                if ck == fk or (isinstance(ck, tuple) and ck[0] == fk):
                    self._cache.pop(ck, None)

    def tick(self) -> None:
        """Clean expired values, or specific entries."""
        now = Instant.now().timestamp()
        if now < self._lasttick:
            return
        self._lasttick = now + 60  # once a minute at most

        pop = [k for k, (e, _) in self._cache.items() if now > e]
        for key in pop:
            self._cache.pop(key)

    def __getitem__(self, key: KT) -> RT:
        """Get a value from the cache."""
        self.tick()
        _, val = self._cache[key]
        return val

    def get(self, key: KT) -> RT | None:
        """Get."""
        self.tick()
        res = self._cache.get(key)
        return res[1] if res else None

    def __setitem__(self, key: KT, value: RT) -> None:
        """Set a value in the cache."""
        expiry = Instant.now().timestamp() + self.minutes * 60
        self._cache[key] = expiry, value

    def get_as[T](
        self,
        key: KT,
        _cast_as: Callable[..., Awaitable[T]] | type[T],
        *,
        minutes: int = 0,
    ) -> tuple[T | None, Callable[[T], T]]:
        """Get a value."""
        self.tick()
        _, res = self._cache.get(key, (None, None))
        retval = (
            list(res)
            if isinstance(res, list)
            else res.copy()
            if isinstance(res, dict)
            else res
        )

        def set_it(val: T) -> T:
            """Set the value."""
            self.__setitem__(key, cast(RT, val))
            return val

        return cast(T, retval), set_it


def cache_return[RT, **P](
    minutes: int = 0,
) -> Callable[[Callable[P, Awaitable[RT]]], Callable[P, Awaitable[RT]]]:
    """Cache the return for x minutes."""

    def decorator(
        func: Callable[P, Awaitable[RT]],
    ) -> Callable[P, Awaitable[RT]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            ckey = (func.__qualname__,)
            res, setcache = CACHE.get_as(ckey, func, minutes=minutes)
            if res is None:
                res = await func(*args, **kwargs)
                setcache(res)
            return res

        return wrapper

    return decorator


CACHE = CacheDict[str | tuple, Any](minutes=30)
