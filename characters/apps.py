from django.apps import AppConfig


class CharactersConfig(AppConfig):
    name = 'characters'

    def ready(self):
        from django.contrib.auth.models import User
        from .worlds import profile_for
        User.add_to_class('playerprofile',property(profile_for))
