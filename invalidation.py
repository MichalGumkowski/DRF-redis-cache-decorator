from django.core.cache import cache

from .key_construction import get_user_cache_key, get_model_cache_key


def invalidate_model_cache(model):
    """
    Invalidates all model related caches.
    :param model: Model class
    """
    model_name = get_model_cache_key(model)
    invalidate_cache_key_pattern(model_name)


def invalidate_cache_key_pattern(cache_key):
    """
    Invalidates all patterns of specific cache_key
    :param cache_key: cache key to invalidate, including those,
    which have key's pattern
    """
    cache.delete_pattern(f'*{cache_key}*')


def invalidate_user_related_cache(user):
    """
    Invalidates all user related cache
    :param user: Specific user instance
    """
    user_cache_key = get_user_cache_key(user)
    invalidate_cache_key_pattern(user_cache_key)
