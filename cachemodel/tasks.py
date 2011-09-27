import pprint

from celery.task import Task
from celery.registry import tasks
from django.core.cache import cache

from cachemodel import CACHE_FOREVER_TIMEOUT, CACHEMODEL_DIRTY_SUFFIX, CACHEMODEL_FORCE_UPDATE_COOKIE

class UpdateGetCached(Task):
    def run(self, *args, **kwargs):
        cache_update = kwargs.get('cache_update',None)
        if cache_update is None:
            raise AttributeError()


        # mark the entry so that the cached_method decorator will know to force update the cache
        cache.set(cache_update['key']+CACHEMODEL_DIRTY_SUFFIX, CACHEMODEL_FORCE_UPDATE_COOKIE, CACHE_FOREVER_TIMEOUT)

        if cache_update.get('is_manager',True):
            method = getattr(cache_update['model']._default_manager, cache_update['function'])

            meth_args = cache_update.get('args',[])
            meth_kwargs = cache_update.get('kwargs',{})
            obj = method(*meth_args, **meth_kwargs)
            cache.set(cache_update['key'], obj, CACHE_FOREVER_TIMEOUT)
        else:
            pprint.pprint(cache_update)


tasks.register(UpdateGetCached)
