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
from cachemodel import CACHE_TIMEOUT
from django.utils.encoding import force_unicode
from hashlib import md5
from django.core.cache import cache

def cached_method(cache_timeout=None, cache_key=None):
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
      cache_timeout -- the number of seconds to keep the cached data.
          A project-wide default may be set once using the cachemodel.set_cache_timeout
          method. If this default is set, cache_timeout is optional.
      cache_key -- a key for the cached method, it will be inside the object's namespace via CacheModel.ns_cache_key().
          If not specified, uses the target method's name.
    
    """
    func = None
    if callable(cache_timeout):
        func = cache_timeout
        cache_timeout = CACHE_TIMEOUT
    elif cache_timeout is None:
        cache_timeout = CACHE_TIMEOUT
    
    if cache_timeout is None:
        raise ValueError("Cache timeout must be specified.")
    
    def decorator(cache_key, target):
        if cache_key == None:
            cache_key = target.__name__

        @wraps(target)
        def wrapper(self, *args, **kwargs):
            cached = kwargs.pop('cached', True)
            chunk = None
            
            arg_suffix = md5(':'.join(force_unicode(v) for v in (list(args) + kwargs.items()))).hexdigest()
            key = self.ns_cache_key(wrapper.cache_key + arg_suffix)

            if cached:
                chunk = cache.get(key)
            
            if chunk is None:
                chunk = target(self, *args, **kwargs)
                cache.set(key, chunk, cache_timeout)
            
            return chunk
        wrapper.cache_key = cache_key
        return wrapper
    
    return decorator(cache_key, func) if func is not None \
        else curry(decorator, cache_key)


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
