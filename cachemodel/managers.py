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

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils.functional import curry
from cachemodel import key_function_memcache_compat
from cachemodel import ns_cache

class CacheModelManager(models.Manager):
    """Manager for use with CacheModel"""
    def get_by(self, field_name, field_value, cache_timeout=None):
        """A convienence function for looking up an object by a particular field

        If the object is in the cache, returned the cached version.
        If the object is not in the cache, do a basic .get() call and store it in the cache.

        Fields used for lookup will be stored in the special cache, '__cached_field_names__'
        so they can be automatically purged on the object's flush_cache() method
        """
        if cache_timeout is None:
            cache_timeout = getattr(settings, 'CACHE_TIMEOUT', 900)

        # cache the field name that was used so flush_cache can purge them automatically
        key = self.model.cache_key("__cached_field_names__")
        cached_field_names = cache.get(key)
        if cached_field_names is None:
            cached_field_names = set()
        cached_field_names.add(field_name)
        cache.set(key, cached_field_names, cache_timeout)

        key = self.model.cache_key("by_" + field_name, field_value)
        obj = cache.get(key)
        if obj is None:
            obj = self.get(**{field_name: field_value})
            cache.set(key_function_memcache_compat(key), obj, cache_timeout)
        return obj

    def ns_cache_key(self, *args):
        """Return a cache key inside the model class's namespace."""
        return ns_cache.ns_key(self.model.cache_key(), args)

    def __getattr__(self, name):
        """
        Allows for calling objects.get_by_pk(...) instead of objects..get_by('pk', ...),
        where ``pk`` is any field.
        """
        if name.startswith('get_by_'):
            # The first time this is called for a field,
            # the resulting curried method is actually
            # added to this instance of the manager.
            new_func = curry(self.get_by, name[7:])
            setattr(self, name, new_func)
            return new_func

        raise AttributeError
