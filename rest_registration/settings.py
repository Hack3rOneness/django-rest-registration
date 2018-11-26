from django.conf import settings as root_settings
from django.test.signals import setting_changed
from rest_framework.settings import perform_import

from rest_registration.settings_fields import SETTINGS_FIELDS

DEFAULTS = {f.name: f.default for f in SETTINGS_FIELDS}
IMPORT_STRINGS = [f.name for f in SETTINGS_FIELDS if f.import_string]


class NestedSettings(object):
    def __init__(
            self, user_settings, defaults, import_strings,
            root_setting_name):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults
        self.import_strings = import_strings
        self.root_setting_name = root_setting_name

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(
                root_settings,
                self.root_setting_name,
                {},
            )
        return self._user_settings

    def reset_user_settings(self):
        if hasattr(self, '_user_settings'):
            del self._user_settings

    def reset_attr_cache(self):
        for key in self.defaults.keys():
            if hasattr(self, key):
                delattr(self, key)

    def __getattr__(self, attr):
        if attr not in self.defaults.keys():
            raise AttributeError(
                "Invalid {self.root_setting_name} setting: '{attr}'".format(
                    self=self, attr=attr))

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Cache the result
        setattr(self, attr, val)
        return val


registration_settings = NestedSettings(
    None, DEFAULTS, IMPORT_STRINGS,
    root_setting_name='REST_REGISTRATION')


def settings_changed_handler(*args, **kwargs):
    registration_settings.reset_user_settings()
    registration_settings.reset_attr_cache()


setting_changed.connect(settings_changed_handler)
