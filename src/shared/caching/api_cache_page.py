from django.views.decorators.cache import cache_page


NO_CACHE = cache_page(0)
ONE_HOUR_CACHE = cache_page(60 * 60)            # 1 hour
LONG_TIME_CACHE = cache_page(60*60*24*7)        # 7 days


