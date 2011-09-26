from django.core.management.base import BaseCommand, CommandError
from django.db import models
import itertools

class Command(BaseCommand):
    help = 'warm the cache for cachemodels'

    def handle(self, *args, **options):
        model_classes = itertools.chain(*(models.get_models(app) for app in models.get_apps()))

        for model in model_classes:
            method = getattr(model._default_manager, 'warm_cache', None)
            if callable(method):
                method()
