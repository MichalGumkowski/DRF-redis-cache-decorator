from inspect import signature

from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import APIView

from ..decorators import _get_response_dict, RESPONSE_KEY_TRANSLATION

User = get_user_model()


class TestDecorators(APITestCase):

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

    def test_get_response_dict_properly_translates_keys(self):
        response_signature = signature(Response)
        response_proper_parameters = response_signature.parameters.keys()

        test_response = Response('test')
        translated_response = _get_response_dict(test_response)

        self.assertEqual(set(response_proper_parameters), set(translated_response.keys()))

    def test_get_response_dict_doesnt_change_values_of_parameters(self):
        response_signature = signature(Response)
        response_proper_keys = response_signature.parameters.keys()

        test_response = Response('test')

        response_values = []
        response_keys = RESPONSE_KEY_TRANSLATION.keys()

        for key in response_proper_keys:
            if key in response_keys:
                response_values.append(getattr(test_response, RESPONSE_KEY_TRANSLATION[key]))

        translated_response = _get_response_dict(test_response)
        translated_response_values = [translated_response[key]
                                      for key in translated_response.keys()]

        self.assertEqual(response_values, translated_response_values)
