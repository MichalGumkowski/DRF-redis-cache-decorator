from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.utils.decorators import method_decorator
from model_mommy import mommy
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import APIView

from ..key_construction import (_CACHE_SEPARATOR as DEFAULT_CACHE_SEPARATOR,
                                _add_param_key_to_cache_key,
                                _add_request_method_to_cache_key,
                                _add_language_to_cache_key,
                                _add_user_to_cache_key,
                                _add_queryparams_to_cache_key,
                                _add_model_dependencies_to_cache_key,
                                get_model_cache_key,
                                get_user_cache_key,
                                get_base_cache_key_for_function,
                                get_cache_key_for_decorated_function,
                                )
from ..utils import get_request_lang

User = get_user_model()


class TestKeyConstruction(APITestCase):

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

    def setUp(self):
        self.cache_key = "cache_key."

    def test_add_param_key_to_cache_key_adds_param_to_cache_key(self):
        param_key = "param_key"

        new_key = _add_param_key_to_cache_key(self.cache_key, param_key)
        proper_key = self.cache_key + "param_key" + DEFAULT_CACHE_SEPARATOR

        self.assertEqual(new_key, proper_key)

    def test_add_request_method_to_cache_key_adds_method_to_cache_key(self):
        get_request = self.get_request()
        post_request = self.get_request(method='post')

        get_cache_key = _add_request_method_to_cache_key(self.cache_key, get_request)
        post_cache_key = _add_request_method_to_cache_key(self.cache_key, post_request)

        get_request_key = "method:GET"
        post_request_key = "method:POST"

        self.assertIn(get_request_key, get_cache_key)
        self.assertIn(post_request_key, post_cache_key)

    def test_add_language_to_cache_key_adds_language_to_cache_key(self):
        request_with_lang = self.get_request(HTTP_ACCEPT_LANGUAGE='some_langs')
        request_without_lang = self.get_request(method='post')

        key_with_lang = _add_language_to_cache_key(self.cache_key, request_with_lang)
        key_without_lang = _add_language_to_cache_key(self.cache_key, request_without_lang)

        lang_of_request_with_lang = get_request_lang(request_with_lang)
        lang_of_request_without_lang = get_request_lang(request_without_lang)

        proper_key_with_lang = "lang:" + lang_of_request_with_lang
        proper_key_without_lang = "lang:" + lang_of_request_without_lang

        self.assertIn(proper_key_with_lang, key_with_lang)
        self.assertIn(proper_key_without_lang, key_without_lang)

    def test_add_user_to_cache_key_doesnt_add_user_key_with_request_and_anonymous_user(self):
        request = self.get_request()
        assert request.user.is_anonymous

        key_without_user = _add_user_to_cache_key(self.cache_key, request)
        default_param_key_of_user = "user"

        self.assertNotIn(default_param_key_of_user, key_without_user)

    def test_add_user_to_cache_key_adds_user_key_with_request_and_authenticated_user(self):
        user = mommy.make(User)
        assert not user.is_anonymous

        request = self.get_request(user=user)

        key_with_user = _add_user_to_cache_key(self.cache_key, request)
        proper_key_with_user = f"user:{user.id}"

        self.assertIn(proper_key_with_user, key_with_user)

    def test_add_user_to_cache_key_doesnt_add_user_key_with_anonymous_user_passed(self):
        request = self.get_request()
        user = request.user
        assert user.is_anonymous

        key_without_user = _add_user_to_cache_key(self.cache_key, user=user)
        default_param_key_of_user = "user"

        self.assertNotIn(default_param_key_of_user, key_without_user)

    def test_add_user_to_cache_key_adds_user_key_with_authenticated_user_passed(self):
        user = mommy.make(User)
        assert not user.is_anonymous

        key_with_user = _add_user_to_cache_key(self.cache_key, user=user)
        proper_key_with_user = f"user:{user.id}"

        self.assertIn(proper_key_with_user, key_with_user)

    def test_add_user_to_cache_key_raises_assertion_error_when_neither_request_nor_user_are_passed(self):
        with self.assertRaises(AssertionError):
            dummy = _add_user_to_cache_key(self.cache_key)

    def test_add_queryparams_to_cache_key_doesnt_add_anything_if_no_params_are_passed(self):
        request = self.get_request()

        key_without_params = _add_queryparams_to_cache_key(self.cache_key, request)

        self.assertEqual(self.cache_key, key_without_params)

    def test_add_queryparams_to_cache_key_add_param_if_one_is_passed(self):
        request = self.get_request(url="/?k=val")

        key_with_param = _add_queryparams_to_cache_key(self.cache_key, request)
        proper_key_with_param = "k:val"

        self.assertIn(proper_key_with_param, key_with_param)

    def test_add_queryparams_to_cache_key_add_params_if_several_passed(self):
        request = self.get_request(url="/?k=val&w=other_val&x=no_val")

        key_with_param = _add_queryparams_to_cache_key(self.cache_key, request)

        k_param_key = "k:val"
        w_param_key = "w:other_val"
        x_param_key = "x:no_val"

        self.assertIn(k_param_key, key_with_param)
        self.assertIn(w_param_key, key_with_param)
        self.assertIn(x_param_key, key_with_param)

    def test_add_queryparams_to_cache_key_doesnt_care_about_params_order_in_url(self):
        # TODO: Write in a loop when not tired ...
        request_one = self.get_request(url="/?k=val&w=other_val&x=no_val")
        request_two = self.get_request(url="/?k=val&x=no_val&w=other_val")
        request_three = self.get_request(url="/?w=other_val&x=no_val&k=val")
        request_four = self.get_request(url="/?w=other_val&k=val&x=no_val")
        request_five = self.get_request(url="/?k=val&x=no_val&w=other_val")
        request_six = self.get_request(url="/?k=val&w=other_val&x=no_val")

        key_with_param_one = _add_queryparams_to_cache_key(self.cache_key, request_one)
        key_with_param_two = _add_queryparams_to_cache_key(self.cache_key, request_two)
        key_with_param_three = _add_queryparams_to_cache_key(self.cache_key, request_three)
        key_with_param_four = _add_queryparams_to_cache_key(self.cache_key, request_four)
        key_with_param_five = _add_queryparams_to_cache_key(self.cache_key, request_five)
        key_with_param_six = _add_queryparams_to_cache_key(self.cache_key, request_six)

        k_param_key = "k:val"
        w_param_key = "w:other_val"
        x_param_key = "x:no_val"

        k_pos_in_one = key_with_param_one.find(k_param_key)
        w_pos_in_one = key_with_param_one.find(w_param_key)
        x_pos_in_one = key_with_param_one.find(x_param_key)

        k_pos_in_two = key_with_param_two.find(k_param_key)
        w_pos_in_two = key_with_param_two.find(w_param_key)
        x_pos_in_two = key_with_param_two.find(x_param_key)

        k_pos_in_three = key_with_param_three.find(k_param_key)
        w_pos_in_three = key_with_param_three.find(w_param_key)
        x_pos_in_three = key_with_param_three.find(x_param_key)

        k_pos_in_four = key_with_param_four.find(k_param_key)
        w_pos_in_four = key_with_param_four.find(w_param_key)
        x_pos_in_four = key_with_param_four.find(x_param_key)

        k_pos_in_five = key_with_param_five.find(k_param_key)
        w_pos_in_five = key_with_param_five.find(w_param_key)
        x_pos_in_five = key_with_param_five.find(x_param_key)

        k_pos_in_six = key_with_param_six.find(k_param_key)
        w_pos_in_six = key_with_param_six.find(w_param_key)
        x_pos_in_six = key_with_param_six.find(x_param_key)

        self.assertTrue(k_pos_in_one == k_pos_in_two ==
                        k_pos_in_three == k_pos_in_four ==
                        k_pos_in_five == k_pos_in_six)
        self.assertNotEqual(k_pos_in_one, -1)

        self.assertTrue(w_pos_in_one == w_pos_in_two ==
                        w_pos_in_three == w_pos_in_four ==
                        w_pos_in_five == w_pos_in_six)
        self.assertNotEqual(w_pos_in_one, -1)

        self.assertTrue(x_pos_in_one == x_pos_in_two ==
                        x_pos_in_three == x_pos_in_four ==
                        x_pos_in_five == x_pos_in_six)
        self.assertNotEqual(x_pos_in_one, -1)

    def test_add_model_dependencies_to_cache_key_doesnt_add_anything_if_no_models_are_passed(self):
        key_without_models = _add_model_dependencies_to_cache_key(self.cache_key, [])

        self.assertEqual(self.cache_key, key_without_models)

    def test_add_model_dependencies_to_cache_key_raises_assertion_error_if_non_iterable_is_passed(self):
        with self.assertRaises(AssertionError):
            dummy = _add_model_dependencies_to_cache_key(self.cache_key, 2)

    def test_add_model_dependencies_to_cache_key_works_well_with_one_element(self):
        model_dependencies = [User, ]

        key_with_models = _add_model_dependencies_to_cache_key(self.cache_key, model_dependencies)

        model_cache_key = get_model_cache_key(User)
        model_dependencies_cache_key = f"dependent:{str([model_cache_key])}"

        self.assertIn(model_cache_key, key_with_models)
        self.assertIn(model_dependencies_cache_key, key_with_models)

    def test_add_model_dependencies_to_cache_key_works_well_with_several_elements(self):
        model_dependencies = [User, Group, Permission]

        key_with_models = _add_model_dependencies_to_cache_key(self.cache_key, model_dependencies)

        user_model_cache_key = get_model_cache_key(User)
        group_model_cache_key = get_model_cache_key(Group)
        permission_model_cache_key = get_model_cache_key(Permission)

        dependencies_names = [user_model_cache_key, group_model_cache_key, permission_model_cache_key]

        model_dependencies_cache_key = f"dependent:{str(dependencies_names)}"

        self.assertIn(user_model_cache_key, key_with_models)
        self.assertIn(group_model_cache_key, key_with_models)
        self.assertIn(permission_model_cache_key, key_with_models)

        self.assertIn(model_dependencies_cache_key, key_with_models)

    def test_get_user_cache_key_returns_proper_key(self):
        user = mommy.make(User)

        proper_user_key = _add_user_to_cache_key("", user=user)
        user_key = get_user_cache_key(user)

        self.assertEqual(proper_user_key, user_key)

    def test_get_user_cache_key_raises_assertion_error_when_non_user_instance_is_passed(self):
        permission = mommy.make(Permission)

        with self.assertRaises(AssertionError):
            dummy = get_user_cache_key(permission)

    def test_get_model_cache_key_returns_proper_key(self):
        proper_key = f"{User._meta.app_label}.{User.__name__}"
        model_key = get_model_cache_key(User)

        self.assertEqual(model_key, proper_key)

    def test_get_base_cache_key_for_function_returns_proper_key_if_identifier_is_passed(self):
        func_kwargs = {'id': 'some_id'}
        identifier = func_kwargs.get('id')

        def some_func():
            pass

        key_for_func = get_base_cache_key_for_function(some_func, identifier=identifier)
        proper_key_without_identifier = f"{self.__module__}.some_func{DEFAULT_CACHE_SEPARATOR}"
        proper_key = _add_param_key_to_cache_key(proper_key_without_identifier, str(identifier))

        self.assertEqual(key_for_func, proper_key)

    def test_get_base_cache_key_for_function_returns_proper_key_if_no_identifier_is_passed(self):
        def some_func():
            pass

        key_for_func = get_base_cache_key_for_function(some_func)
        proper_key = f"{self.__module__}.some_func{DEFAULT_CACHE_SEPARATOR}"

        self.assertEqual(key_for_func, proper_key)

    def test_get_cache_key_for_decorated_function_with_default_params(self):
        request = self.get_request()

        def decorator(func):
            def wrapped(request, *args, **kwargs):
                return func(request, *args, **kwargs)

            return wrapped

        @method_decorator(decorator)
        def some_func(request, *args, **kwargs):
            return "testing"

        func_key = get_cache_key_for_decorated_function(some_func, request)

        proper_key_of_function = get_base_cache_key_for_function(some_func)
        proper_key = _add_request_method_to_cache_key(proper_key_of_function, request)

        self.assertEqual(func_key, proper_key)

    def test_get_cache_key_for_decorated_function_with_cache_language(self):
        request = self.get_request()

        def decorator(func):
            def wrapped(request, *args, **kwargs):
                return func(request, *args, **kwargs)

            return wrapped

        @method_decorator(decorator)
        def some_func(request, *args, **kwargs):
            return "testing"

        func_key = get_cache_key_for_decorated_function(some_func,
                                                        request,
                                                        cache_language=True)

        proper_key_of_function = get_base_cache_key_for_function(some_func)
        proper_key_with_request = _add_request_method_to_cache_key(proper_key_of_function, request)
        proper_key = _add_language_to_cache_key(proper_key_with_request, request)

        self.assertEqual(func_key, proper_key)

    def test_get_cache_key_for_decorated_function_with_cache_user(self):
        user = mommy.make(User)
        request = self.get_request(user=user)

        def decorator(func):
            def wrapped(request, *args, **kwargs):
                return func(request, *args, **kwargs)

            return wrapped

        @method_decorator(decorator)
        def some_func(request, *args, **kwargs):
            return "testing"

        func_key = get_cache_key_for_decorated_function(some_func,
                                                        request,
                                                        cache_user=True)

        proper_key_of_function = get_base_cache_key_for_function(some_func)
        proper_key_with_request = _add_request_method_to_cache_key(proper_key_of_function, request)
        proper_key = _add_user_to_cache_key(proper_key_with_request, request)

        self.assertEqual(func_key, proper_key)

    def test_get_cache_key_for_decorated_function_with_queryparams(self):
        request = self.get_request(url="/?k=val")

        def decorator(func):
            def wrapped(request, *args, **kwargs):
                return func(request, *args, **kwargs)

            return wrapped

        @method_decorator(decorator)
        def some_func(request, *args, **kwargs):
            return "testing"

        func_key = get_cache_key_for_decorated_function(some_func,
                                                        request,
                                                        cache_queryparams=True)

        proper_key_of_function = get_base_cache_key_for_function(some_func)
        proper_key_with_request = _add_request_method_to_cache_key(proper_key_of_function, request)
        proper_key = _add_queryparams_to_cache_key(proper_key_with_request, request)

        self.assertEqual(func_key, proper_key)

    def test_get_cache_key_for_decorated_function_with_model_dependencies(self):
        request = self.get_request()
        model_dependencies = [User, Permission]

        def decorator(func):
            def wrapped(request, *args, **kwargs):
                return func(request, *args, **kwargs)

            return wrapped

        @method_decorator(decorator)
        def some_func(request, *args, **kwargs):
            return "testing"

        func_key = get_cache_key_for_decorated_function(some_func,
                                                        request,
                                                        model_dependencies=model_dependencies)

        proper_key_of_function = get_base_cache_key_for_function(some_func)
        proper_key_with_request = _add_request_method_to_cache_key(proper_key_of_function, request)
        proper_key = _add_model_dependencies_to_cache_key(proper_key_with_request,
                                                          model_dependencies)

        self.assertEqual(func_key, proper_key)

    def test_get_cache_key_for_decorated_function_with_identifier(self):
        request = self.get_request()
        identifier = "some_identifier"

        def decorator(func):
            def wrapped(request, *args, **kwargs):
                return func(request, *args, **kwargs)

            return wrapped

        @method_decorator(decorator)
        def some_func(request, *args, **kwargs):
            return "testing"

        func_key = get_cache_key_for_decorated_function(some_func,
                                                        request,
                                                        identifier=identifier)

        proper_key_of_function = get_base_cache_key_for_function(some_func, identifier)
        proper_key = _add_request_method_to_cache_key(proper_key_of_function, request)

        self.assertEqual(func_key, proper_key)

    def test_get_cache_key_for_decorated_function_with_all_params(self):
        user = mommy.make(User)
        request = self.get_request(url="/?k=val", user=user)
        model_dependencies = [User, Permission]
        identifier = "some_identifier"

        def decorator(func):
            def wrapped(request, *args, **kwargs):
                return func(request, *args, **kwargs)

            return wrapped

        @method_decorator(decorator)
        def some_func(request, *args, **kwargs):
            return "testing"

        func_key = get_cache_key_for_decorated_function(some_func,
                                                        request,
                                                        cache_language=True,
                                                        cache_user=True,
                                                        cache_queryparams=True,
                                                        model_dependencies=model_dependencies,
                                                        identifier=identifier)

        proper_key_of_function = get_base_cache_key_for_function(some_func, identifier)
        proper_key_with_request = _add_request_method_to_cache_key(proper_key_of_function, request)
        proper_key_with_lang = _add_language_to_cache_key(proper_key_with_request, request)
        proper_key_with_user = _add_user_to_cache_key(proper_key_with_lang, request)
        proper_key_with_queryparams = _add_queryparams_to_cache_key(proper_key_with_user, request)
        proper_key = _add_model_dependencies_to_cache_key(proper_key_with_queryparams, model_dependencies)

        self.assertEqual(func_key, proper_key)
