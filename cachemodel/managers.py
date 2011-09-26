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

from cachemodel import CACHE_FOREVER_TIMEOUT
from django.core.cache import cache
from django.db import models
from cachemodel import ns_cache

class CacheModelManager(models.Manager):
    """Manager for use with CacheModel"""
    use_for_related_fields = True


    def _generate_function_signature(self, *args, **kwargs):
        """generate a unique signature based on arguments"""
        signature = ",".join(args)+":"+ ":".join("%s=%s" % (field, value) for field,value in kwargs.items())

        # cache the signature so flush_cache can flush them all automatically
        signatures_key = self.model.cache_key("__cached_signatures__")
        cached_signatures = cache.get(signatures_key)
        if cached_signatures is None:
            cached_signatures = set()
        cached_signatures.add(signature)
        cache.set(signatures_key, cached_signatures, CACHE_FOREVER_TIMEOUT)

        return signature

    def get_cached(self, *args, **kwargs):
        """Wrapper around get() that caches the result for future calls"""
        signature = self._generate_function_signature(*args, **kwargs)

        cache_key = self.model.cache_key("get_cached", signature)
        obj = cache.get(cache_key)
        if obj is None:
            obj = super(CacheModelManager, self).get(*args, **kwargs)
            cache.set(cache_key, obj, CACHE_FOREVER_TIMEOUT)
        return obj


    def ns_cache_key(self, *args):
        """Return a cache key inside the model class's namespace."""
        return ns_cache.ns_key(self.model.cache_key(), args)
