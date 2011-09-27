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
from django.utils.encoding import smart_str
from django.conf import settings
from django.core.cache import cache

VERSION = (0,9,8)

CACHE_FOREVER_TIMEOUT = getattr(settings, 'CACHE_FOREVER_TIMEOUT', 60*60*24*365) # one year
CACHEMODEL_CELERY_SUPPORT = getattr(settings, 'CACHEMODEL_CELERY_SUPPORT', False)



CACHEMODEL_DIRTY_SUFFIX = '__is_dirty__'
CACHEMODEL_FORCE_UPDATE_COOKIE = '__force_update__'



def key_function_memcache_compat(value):
    """
    Encode a value into a memcached key-compatible string.
    """
    return smart_str(value, encoding='ascii', errors='xmlcharrefreplace')


def generate_function_signature_key(prefix, cache_key_func, *args, **kwargs):
    """generate a unique signature based on arguments given, then save a copy in the cache to iterate over later"""

    parts = []
    parts.append(",".join(key_function_memcache_compat(a) for a in args))
    parts.append('&'.join("%s=%s" % (field, value) for field,value in kwargs.items()))
    signature = ':'.join(parts)
    cache_key = cache_key_func(prefix, signature)

    # cache the signature so flush_cache can flush them all automatically
    signatures_key = cache_key_func("__cached_signatures_%s__" % (prefix,))
    cached_signatures = cache.get(signatures_key)
    if cached_signatures is None:
        cached_signatures = set()
    cached_signatures.add(cache_key)
    cache.set(signatures_key, cached_signatures, CACHE_FOREVER_TIMEOUT)

    return cache_key

def mark_all_signatures_as_dirty(prefix, cache_key_func):
    signatures_key = cache_key_func("__cached_signatures_%s__" % (prefix,))
    cached_signatures = cache.get(signatures_key)
    if cached_signatures is not None:
        for signature in cached_signatures:
            cache.set(signature+CACHEMODEL_DIRTY_SUFFIX, True, CACHE_FOREVER_TIMEOUT)
