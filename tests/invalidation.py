from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from model_mommy import mommy
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import APIView

from ..invalidation import invalidate_user_related_cache, invalidate_cache_key_pattern, invalidate_model_cache
from ..key_construction import (get_model_cache_key,
                                get_user_cache_key,
                                )

User = get_user_model()


class TestInvalidation(APITestCase):

    def get_request(self, url="/", method="get", user=None, *args, **kwargs):
        client = APIClient()
        if user is not None:
            client.force_authenticate(user=user)

        request_method_dict = {
            "get": client.get,
            "post": client.post,
            "patch": client.patch,
            "put": client.put,
            "delete": client.delete
        }

        request_method = request_method_dict[method]
        base_request = request_method(url, *args, **kwargs).wsgi_request

        return APIView().initialize_request(base_request)

    def test_invalidate_cache_key_pattern_invalidates_keys_with_particular_pattern_only(self):
        cache_pattern = 'PATTERN'
        string_to_add = '1!Q%A'
        dummy_val = "dummy"

        cache_keys = dict(
            cache_key_equal_pattern=cache_pattern,
            cache_key_with_pattern_at_end=string_to_add + cache_pattern,
            cache_key_with_pattern_at_front=cache_pattern + string_to_add,
            cache_key_with_pattern_in_middle=string_to_add + cache_pattern + string_to_add,
            cache_key_with_multiple_patterns=(string_to_add + cache_pattern +
                                              cache_pattern + string_to_add +
                                              cache_pattern + string_to_add),
            cache_key_without_pattern=string_to_add,
        )

        for cache_key in cache_keys.values():
            cache.set(cache_key, dummy_val)

        invalidate_cache_key_pattern(cache_pattern)

        self.assertIs(cache.get(cache_keys['cache_key_equal_pattern']), None)
        self.assertIs(cache.get(cache_keys['cache_key_with_pattern_at_end']), None)
        self.assertIs(cache.get(cache_keys['cache_key_with_pattern_at_front']), None)
        self.assertIs(cache.get(cache_keys['cache_key_with_pattern_in_middle']), None)
        self.assertIs(cache.get(cache_keys['cache_key_with_multiple_patterns']), None)
        self.assertEqual(cache.get(cache_keys['cache_key_without_pattern']),
                         dummy_val)

        for cache_key in cache_keys.items():
            cache.delete(cache_key)

    def test_invalidate_model_cache_invalidates_model_cache(self):
        model_to_invalidate = User
        model_cache_key = get_model_cache_key(model_to_invalidate)

        model_still_valid = Permission
        other_model_cache_key = get_model_cache_key(model_still_valid)

        string_to_add = '1!Q%A'
        dummy_val = 'dummy'

        cache_keys = dict(
            cache_key_with_model=model_cache_key,
            cache_key_with_model_at_front=model_cache_key + string_to_add,
            cache_key_with_model_at_back=string_to_add + model_cache_key,
            cache_key_with_model_in_middle=string_to_add + model_cache_key + string_to_add,
            cache_key_with_other_model=other_model_cache_key,
            cache_key_without_model=string_to_add,
        )

        for cache_key in cache_keys.values():
            cache.set(cache_key, dummy_val)

        invalidate_model_cache(model_to_invalidate)

        self.assertIs(cache.get(cache_keys['cache_key_with_model']), None)
        self.assertIs(cache.get(cache_keys['cache_key_with_model_at_front']), None)
        self.assertIs(cache.get(cache_keys['cache_key_with_model_at_back']), None)
        self.assertIs(cache.get(cache_keys['cache_key_with_model_in_middle']), None)
        self.assertEqual(cache.get(cache_keys['cache_key_without_model']),
                         dummy_val),
        self.assertEqual(cache.get(cache_keys['cache_key_with_other_model']),
                         dummy_val)

        for cache_key in cache_keys.items():
            cache.delete(cache_key)

    def test_invalidate_user_related_cache_invalidates_user_related_cache(self):
        user_to_invalidate = mommy.make(User)
        user_cache_key = get_user_cache_key(user_to_invalidate)

        user_still_valid = mommy.make(User)
        other_user_cache_key = get_user_cache_key(user_still_valid)

        string_to_add = '1!Q%A'
        dummy_val = 'dummy'

        cache_keys = dict(
            cache_key_with_user=user_cache_key,
            cache_key_with_user_at_front=user_cache_key + string_to_add,
            cache_key_with_user_at_back=string_to_add + user_cache_key,
            cache_key_with_user_in_middle=string_to_add + user_cache_key + string_to_add,
            cache_key_with_other_user=other_user_cache_key,
            cache_key_without_user=string_to_add,
        )

        for cache_key in cache_keys.values():
            cache.set(cache_key, dummy_val)

        invalidate_user_related_cache(user_to_invalidate)

        self.assertIs(cache.get(cache_keys['cache_key_with_user']), None)
        self.assertIs(cache.get(cache_keys['cache_key_with_user_at_front']), None)
        self.assertIs(cache.get(cache_keys['cache_key_with_user_at_back']), None)
        self.assertIs(cache.get(cache_keys['cache_key_with_user_in_middle']), None)
        self.assertEqual(cache.get(cache_keys['cache_key_with_other_user']),
                         dummy_val),
        self.assertEqual(cache.get(cache_keys['cache_key_without_user']),
                         dummy_val)

        for cache_key in cache_keys.items():
            cache.delete(cache_key)
