import logging
from functools import wraps
from inspect import signature

from django.core.cache import cache
from rest_framework.response import Response

from .key_construction import get_cache_key_for_decorated_function

logger = logging.getLogger(__name__)

RESPONSE_KEY_TRANSLATION = {
    "data": "data",
    "status": "status_code",
    "template_name": "template_name",
    "headers": "_headers",
    "exception": "exception",
    "content_type": "content_type",
}


def cache_it(cache_expiration_minutes=60,
             instance_unique_parameter='pk',
             cache_language=True,
             cache_user=True,
             cache_queryparams=True,
             model_dependencies=[],
             valid_response_codes=[200, ],
             valid_request_methods=['GET', ]):
    """
    This decorator checks if there is a cached version of a view in memory - if so it returns it,
    if not - executes the view and saves the response in cache
    :param cache_expiration_minutes: defines time in minutes, for which cache exists
    :param instance_unique_parameter: string, representing an unique parameter,
    which should be used to idenfity an instance (such as pk, slug, etc...)
    :param cache_language: defines, whether the view should be language sensitive
    :param cache_user: defines, whether view should be cached per user
    all non logged users share basic cache
    :param cache_queryparams: defines, whether view should be cached separately
    for different query params. Order does not matter (it is sorted).
    :param model_dependencies: defines, which model changes should invalidate cache.
    Leave empty for time dependent invalidation.
    :param valid_response_codes: iterable, which defines response codes for which
    the view should be cached. Default = [200, ]
    :param valid_request_methods: iterable, which defines request types for which
    the view should be cached. Default = ['GET', ]
    :return: View for requested decorator
    """

    def _method_wrapper(view_func):
        cache_expiration_time = cache_expiration_minutes * 60

        @wraps(view_func)
        def wrapped(request, *args, **kwargs):

            instance_identifier = kwargs.get(instance_unique_parameter, None)

            cache_name = get_cache_key_for_decorated_function(view_func,
                                                              request,
                                                              cache_language=cache_language,
                                                              cache_user=cache_user,
                                                              cache_queryparams=cache_queryparams,
                                                              model_dependencies=model_dependencies,
                                                              identifier=instance_identifier)
            current_cache = cache.get(cache_name)

            if current_cache:
                response_dict = current_cache

            else:

                response = view_func(request, *args, **kwargs)
                response_dict = _get_response_dict(response)

                if (response.status_code in valid_response_codes
                        and request.method in valid_request_methods
                        and response.data):
                    cache.set(cache_name, response_dict, cache_expiration_time)

            return Response(**response_dict)

        return wrapped

    return _method_wrapper


def _get_response_dict(response):
    """
    Private function responsible for translation of response argument keys,
    so they may be user as an arguments for Response function.
    :param response:
    :return:
    """
    response_dict = dict()
    response_signature = signature(Response)

    for name in response_signature.parameters.keys():
        translated_key = RESPONSE_KEY_TRANSLATION.get(name, name)
        response_dict[name] = getattr(response, translated_key)

    return response_dict
