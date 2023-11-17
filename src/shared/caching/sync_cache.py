from django.core.cache import cache


SYNC_CACHE_TIMEOUT = 24 * 60 * 60        # 24 hours


def get_sync_cache_key(user_id, page, size=100):
    return f"sync:{user_id}:{size}:{page}"


def delete_sync_cache_data(user_id):
    keys = cache.keys(f"sync:{user_id}:*")
    if not keys:
        return
    return cache.delete_many(keys=keys)
