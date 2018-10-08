=============================
DRF redis cache decorator
=============================

DRF redis cache decorator is a little library, which simplifies caching of class based views.
Feel free to criticize

Quick start
-----------

| 0. Insert DRF redis cache decorator to your project (will be installable as a package soon)
| 1. Add 'drf_redis_cache_decorator.apps.DRFRedisCacheDecorator' to installed_apps.
| 2. Do following imports on views you want to cache
|   - from django.utils.decorators import method_decorator
|   - from drf_redis_cache_decorator.decorators import cache_it
| 3. Add the decorator to a desired view:
|       @method_decorator(cache_it())
|       def some_view(request, \*args, \*\*kwargs):
|           pass
|
| 4. Customize your cache:
|       @method_decorator(cache_it(
|                     cache_expiration_minutes=60,
|                     instance_unique_parameter='pk',
|                     cache_language=True,
|                     cache_user=True,
|                     cache_queryparams=True,
|                     model_dependencies=[],
|                     valid_response_codes=[200, ],
|                     valid_request_methods=['GET', ]
|       ))
|
|   Where:
|   - cache_expiration_minutes: Time in minutes, which defines the cache existence.
|   - instance_unique_parameter: Unique parameter, which defines, which parameter should be used to identify an instance.
|   - cache_language: defines, if language should be considered when caching.
|   - cache_user: defines, if cache should be user-dependent.
|   - cache_queryparams: defines, if query params should be considered when caching.
|   - model_dependencies: defines the models, which should invalidate the cache.
|   - valid_response_codes: iterable with response codes, which allows to cache the view.
|   - valid_request_methods: iterable with request methods (as uppercase strings) which allows to cache the view.