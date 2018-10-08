import collections
import inspect

from django.contrib.auth import get_user_model

from .utils import get_request_lang

User = get_user_model()

_CACHE_SEPARATOR = "__"


def get_cache_key_for_decorated_function(func,
                                         request,
                                         cache_language=False,
                                         cache_user=False,
                                         cache_queryparams=False,
                                         model_dependencies=[],
                                         identifier=None, ):
    """
    Creates a cache key for given function.
    :param func: The function passed to the decorator
    :param request: request send by client
    :param cache_language: defines, whether view should be cached per language
    :param cache_user: defines, whether view should be cached per user
    all non logged users share basic cache
    :param cache_queryparams: defines, whether view should be cached separately
    for different query params. Order does not matter (it is sorted).
    :param model_dependencies: defines, which models invalidate cache
    of this particular view
    :param identifier: identifier of an instance (if it is a call on instance's view)
    :return: key for function passed to the decorator
    """
    # inspect.getclosurevars is required, because all the views are passed
    # indirectly via @method_decorator
    decorated_func = inspect.getclosurevars(func)[0]['func']

    key = get_base_cache_key_for_function(decorated_func, identifier)
    key = _add_request_method_to_cache_key(key, request)

    if cache_language:
        key = _add_language_to_cache_key(key, request)

    if cache_user:
        key = _add_user_to_cache_key(key, request)

    if cache_queryparams:
        key = _add_queryparams_to_cache_key(key, request)

    if model_dependencies:
        key = _add_model_dependencies_to_cache_key(key, model_dependencies)

    return key


def get_base_cache_key_for_function(func, identifier=None):
    """
    Creates an unique cache key by getting module of a function and it's name
    :param func: Function, that has to be cached
    :param identifier: Optional, identifier passed to the view
    :return: string with module name and func name
    """
    cache_key = f'{func.__module__}.{func.__name__}{_CACHE_SEPARATOR}'
    if identifier is not None:
        cache_key = _add_param_key_to_cache_key(cache_key, str(identifier))
    return cache_key


def get_user_cache_key(user):
    """
    Returns a part of cache key used to identify user.
    :param user: User instance
    :return: Part of cache key used to identify user
    """
    assert isinstance(user, User)
    return _add_user_to_cache_key("", user=user)


def get_model_cache_key(model):
    """
    Returns a part of cache key used to identify mode.
    :param model: model, on which cache depends
    :return: Part of cache key used to identify model
    """
    return f'{model._meta.app_label}.{model.__name__}'


def _add_param_key_to_cache_key(cache_key, param_key):
    """
    :param param_key: cache key of the parameter
    :param cache_key: currenct cache key
    :return: new cache key in a form {cache_key}{_CACHE_SEPARATOR}
    """
    return f'{cache_key}{param_key}{_CACHE_SEPARATOR}'


def _add_request_method_to_cache_key(cache_key, request):
    """
    Adds a request method to cache key
    :param cache_key: current cache key
    :param request: request sent by client
    :return: cache key with added request method
    """
    method = request.method
    param_key = f'method:{method}'
    return _add_param_key_to_cache_key(cache_key, param_key)


def _add_language_to_cache_key(cache_key, request):
    """
    :param cache_key: current cache key
    :param request: request sent by client
    :return: cache key with added language
    """
    language_code = get_request_lang(request)
    param_key = f'lang:{language_code}'
    return _add_param_key_to_cache_key(cache_key, param_key)


def _add_user_to_cache_key(cache_key, request=None, user=None):
    """
    Adds a user's pk to the cache key
    One of the parameters (request or user) has to be passed
    :param cache_key: current cache key
    :param request: request sent by client
    :param user: user, which has to be added
    :return: cache key with added user's username
    """
    assert user or request
    user = user or request.user
    if not user.is_anonymous:
        param_key = f'user:{user.id}'
        cache_key = _add_param_key_to_cache_key(cache_key, param_key)

    return cache_key


def _add_queryparams_to_cache_key(cache_key, request):
    """
    Sorts queryparams and adds them using ".{key}:{value}" pattern
    :param cache_key: current cache key
    :param request: request sent by client
    :return: cache key with added queryparams
    """
    query_params = request.query_params

    for key, value in sorted(query_params.items()):
        param_key = f'{key}:{value}'
        cache_key = _add_param_key_to_cache_key(cache_key, param_key)

    return cache_key


def _add_model_dependencies_to_cache_key(cache_key, model_dependencies):
    """
    Adds model dependencies to cache key.
    :param cache_key: current cache key
    :param model_dependencies: model dependencies passed to the decorator.
    :return: cache key with added model dependencies
    """
    assert isinstance(model_dependencies, collections.Iterable)

    dependencies_names = [get_model_cache_key(model) for model in model_dependencies]

    if dependencies_names:
        param_key = f'dependent:{str(dependencies_names)}'
        cache_key = _add_param_key_to_cache_key(cache_key, param_key)

    return cache_key
