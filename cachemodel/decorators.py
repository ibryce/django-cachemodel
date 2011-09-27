#  Copyright 2010 Concentric Sky, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from functools import wraps
from cachemodel import CACHE_FOREVER_TIMEOUT, CACHEMODEL_DIRTY_SUFFIX, CACHEMODEL_CELERY_SUPPORT, generate_function_signature_key, CACHEMODEL_FORCE_UPDATE_COOKIE
from django.utils.functional import curry
from django.utils.encoding import force_unicode
from hashlib import md5
from django.core.cache import cache
from django.conf import settings


def cached_method(*args, **kwargs):
    """A decorator for CacheModel methods.

     - Builds a key based on cache_key and the object's ns_cache_key() method.
     - Checks the cache for data at that key, if data exists it is returned and the method is never called.
     - If the cache is stale or nonexistent, run the method and cache the result at the key specified.

    May be called with or without arguments, i.e.
        @cached_method
        def some_method(self, ...)

    or
        @cached_method(cache_key='something_else')
        def some_method(self, ...)

    Arguments:
      cache_key -- a key for the cached method, it will be inside the object's namespace via 
                   CacheModel.ns_cache_key() If not specified, uses the target method's name.

    """

    def decorator(cache_key, target):
        if cache_key is None:
            cache_key = target.__name__  # imply the cache_key from the name of target function

        @wraps(target)
        def wrapper(self, *args, **kwargs):
            cache_key = wrapper._cache_key
            key = generate_function_signature_key("cached_method", self.cache_key, *([cache_key] + list(args)), **kwargs)
            is_dirty = cache.get(key+CACHEMODEL_DIRTY_SUFFIX)
            force_update = (is_dirty == CACHEMODEL_FORCE_UPDATE_COOKIE)

            chunk = None

            if not force_update and not is_dirty:
                chunk = cache.get(key)

            if not force_update and is_dirty and CACHEMODEL_CELERY_SUPPORT: # we are dirty, but display the cached one while we update via celery
                chunk = cache.get(key)
                from cachemodel.tasks import UpdateGetCached
                UpdateGetCached.delay(cache_update={
                    'is_manager': hasattr(self, 'model'),
                    'model': self.model if hasattr(self, 'model') else self,
                    'function': target.__name__,
                    'key': key,
                    'args': args,
                    'kwargs': kwargs,
                })


            if force_update or chunk is None:
                chunk = target(self, *args, **kwargs)
                cache.set(key, chunk, CACHE_FOREVER_TIMEOUT)
                cache.delete(key+CACHEMODEL_DIRTY_SUFFIX)
            return chunk
        wrapper._cached_method = True
        wrapper._cache_key = cache_key
        return wrapper

    # if decorator was used without (), we are passed target directly so call with cache_key=None
    if len(args) and callable(args[0]):
        return decorator(cache_key=None, target=args[0])

    # otherwise we were used with (), and passed the key either as a kwarg or args[0] (or None if no args)
    cache_key = kwargs.get('cache_key', None)
    if cache_key is None and len(args) > 0:
        cache_key = args[0]
    return curry(decorator, cache_key)

def denormalized_field(field_name):
    """A decorator for CacheModel methods.

    - pass the field name to denormalized into into the decorator
    - the return of the function will be stored in the database field on each save

    Arguments:
      field_name -- the name of a field on the model that will store the results of the function
    """
    def decorator(target):
        @wraps(target)
        def wrapper(self):
            return target(self)
        wrapper._denormalized_field = True
        wrapper._denormalized_field_name = field_name
        return wrapper
    return decorator
