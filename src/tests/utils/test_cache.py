"""Tests for ``dataplaybook.utils.cache``."""

from dataplaybook.utils.cache import CacheDict


async def _cached_demo_fn() -> str:
    return ""


async def _cached_db_get_presales() -> list[str]:
    return []


def test_cache_dict_clear_all() -> None:
    cache: CacheDict[str, str] = CacheDict()
    cache["a"] = "1"
    cache["b"] = "2"

    cache.clear()

    assert cache.get("a") is None
    assert cache.get("b") is None


def test_cache_dict_clear_exact_key() -> None:
    cache: CacheDict[str, str] = CacheDict()
    cache["keep"] = "yes"
    cache["drop"] = "no"

    cache.clear("drop")

    assert cache.get("keep") == "yes"
    assert cache.get("drop") is None


def test_cache_dict_clear_callable_by_qualname() -> None:
    cache: CacheDict[str | tuple[str, ...], str] = CacheDict()
    qual = _cached_demo_fn.__qualname__
    key_a = (qual, "A")
    key_b = (qual, "B")
    cache[key_a] = "a"
    cache[key_b] = "b"
    cache["other"] = "x"

    cache.clear(_cached_demo_fn)

    assert cache.get(key_a) is None
    assert cache.get(key_b) is None
    assert cache.get("other") == "x"


def test_cache_dict_clear_callable_exact_string_key() -> None:
    """String keys equal to ``__qualname__`` are removed."""
    cache: CacheDict[str, str] = CacheDict()
    cache[_cached_db_get_presales.__qualname__] = "cached"

    cache.clear(_cached_db_get_presales)

    assert cache.get(_cached_db_get_presales.__qualname__) is None


def test_cache_dict_clear_multiple_keys() -> None:
    cache: CacheDict[str, str] = CacheDict()
    cache["one"] = "1"
    cache["two"] = "2"
    cache["three"] = "3"

    cache.clear("one", "three")

    assert cache.get("one") is None
    assert cache.get("two") == "2"
    assert cache.get("three") is None
