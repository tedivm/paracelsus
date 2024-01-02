import os
from typing import Iterable

from django.conf import LazySettings
from django.db import models

from paracelsus.adapters.base import ModelAdapter, Table


class DjangoModelAdapter(ModelAdapter):
    def __init__(self, settings: LazySettings):
        self.settings = settings

    def get_models(self) -> Iterable[models.Model]:
        if hasattr(self, "_models"):
            return self._models  # type: ignore

        import django.apps

        django.apps.apps.populate(installed_apps=self.settings.INSTALLED_APPS)
        self._models = django.apps.apps.get_models()
        return self._models

    @property
    def models(self):
        return self.get_models()

    def tables(self) -> dict[str, "Table"]:
        raise NotImplementedError("yet")

    @classmethod
    def from_settings(cls, settings_module: str) -> "DjangoModelAdapter":
        from django.conf import ENVIRONMENT_VARIABLE, settings

        os.environ[ENVIRONMENT_VARIABLE] = settings_module

        # settings are resolved only after accessing an attribute, so let's do that here.
        print(f":===>{settings.INSTALLED_APPS}")

        return DjangoModelAdapter(settings=settings)
