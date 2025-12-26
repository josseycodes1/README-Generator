import hashlib
from django.core.cache import cache


def make_cache_key(repo_url: str, analysis_data: dict) -> str:
    """
    Create a stable cache key for README generation
    based on repo URL + analyzed structure.
    """
    raw = repo_url + str(sorted(analysis_data.items()))
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"readme:llm:{digest}"


def get_cached_readme(cache_key: str) -> str | None:
    return cache.get(cache_key)


def set_cached_readme(cache_key: str, value: str, ttl: int = 60 * 60 * 24):
    cache.set(cache_key, value, ttl)
