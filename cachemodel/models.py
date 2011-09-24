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

from django.core.cache import cache
from django.db import models
from cachemodel import ns_cache
from cachemodel import key_function_memcache_compat
from cachemodel.managers import CacheModelManager

from cachemodel.decorators import *   # backwards compatability

class CacheModel(models.Model):
    """An abstract model that has convienence functions for dealing with caching."""
    objects = CacheModelManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        #find all the methods decorated with denormalized_field and save them into their respective fields
        for method in _find_denormalized_fields(self):
            setattr(self, method._denormalized_field_name, method(self))
        super(CacheModel, self).save(*args, **kwargs)
        self.flush_cache()

    def delete(self, *args, **kwargs):
        super(CacheModel, self).delete(*args, **kwargs)
        self.flush_cache()

    def flush_cache(self):
        """this method is called on save() and delete(), any cached fields should be expunged here."""
        # lookup the fields that have been cached by .get_by() and purge them
        cached_field_names = cache.get( self.cache_key("__cached_field_names__") ) 
        if cached_field_names is not None:
            for field_name in cached_field_names:
                try:
                    cache.delete( self.cache_key("by_" + field_name, getattr(self, field_name)) )
                except:
                    # try to delete the cache if possible, otherwise...
                    pass

        # Flush the object's cache namespace.
        self.ns_flush_cache()

    def ns_cache_key(self, *args):
        """Return a cache key inside the object's namespace.

        The namespace is built from: The Objects class.__name__ and the Object's PK.
        """
        return ns_cache.ns_key(self.cache_key(self.pk), args)

    def ns_flush_cache(self):   
        """Flush all cache keys inside the object's namespace"""
        ns_cache.ns_flush(self.cache_key(self.pk))

    @classmethod
    def cache_key(cls, *args):
        """
        Generates a cache key from the object's class.__name__ and the arguments given
        """
        vals = [cls.__name__] + [key_function_memcache_compat(arg) for arg in args]
        return '_'.join(vals)

    def __getattr__(self, name):
        if name.startswith('cached_'):
            field_name = name[7:]
            field = self._meta.get_field(field_name)
            if isinstance(field, models.ForeignKey):
                related_model = field.related.parent_model
                related_id = getattr(self, '%s_id' % field_name)
                if hasattr(related_model.objects, 'get_by_pk'):
                    return related_model.objects.get_by_pk(related_id)
                else:
                    return getattr(self, field_name)
        raise AttributeError

def _find_denormalized_fields(instance):
    """helper function that finds all methods decorated with @denormalized_field"""
    non_field_attributes = set(dir(instance.__class__)) - set(instance._meta.get_all_field_names())
    for m in non_field_attributes:
        if hasattr(getattr(instance.__class__, m), '_denormalized_field'):
            yield getattr(instance.__class__, m)


