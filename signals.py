from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .invalidation import invalidate_model_cache, invalidate_user_related_cache

user_model = get_user_model()


@receiver((post_save, post_delete))
def invalidate_model_cache_signal(sender, *args, **kwargs):
    """
    Receiver responsible for invalidating all the cache related to the specific model.
    If User Model sends the signal, function additionaly invalidates all the cache related to that specific user.
    :param sender: Model, which sends the signal
    :param args: all the arguments
    :param kwargs: all the key word arguments
    """
    invalidate_model_cache(sender)
    if issubclass(sender, user_model):
        user = kwargs.get('instance')
        invalidate_user_related_cache(user)
