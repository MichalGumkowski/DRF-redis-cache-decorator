from django.conf import settings


def get_request_lang(request):
    return request.META.get("HTTP_ACCEPT_LANGUAGE", getattr(settings, "LANGUAGE_CODE", ""))
