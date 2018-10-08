from django.apps import AppConfig


class DRFRedisCacheDecorator(AppConfig):
    name = 'drf_redis_cache_decorator'

    def ready(self):
        from .signals import invalidate_model_cache_signal