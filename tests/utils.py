from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import APIView

from ..utils import get_request_lang

User = get_user_model()


class TestUtils(APITestCase):

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

    def test_get_request_lang_returns_language_from_request_if_passed(self):
        request_lang = "some_lang"
        request = self.get_request(HTTP_ACCEPT_LANGUAGE=request_lang)

        lang_from_func = get_request_lang(request)

        self.assertEqual(request_lang, lang_from_func)

    def test_get_request_lang_returns_language_from_settings_if_not_passed(self):
        request = self.get_request()
        settings_lang = getattr(settings, "LANGUAGE_CODE", "")

        lang_from_func = get_request_lang(request)

        self.assertEqual(settings_lang, lang_from_func)
