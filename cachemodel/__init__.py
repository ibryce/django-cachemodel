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

VERSION = (0,9,8)

CACHE_FOREVER_TIMEOUT = getattr(settings, 'CACHE_FOREVER_TIMEOUT', 60*60*24*365) # one year


def key_function_memcache_compat(value):
    """
    Encode a value into a memcached key-compatible string.
    """
    return smart_str(value, encoding='ascii', errors='xmlcharrefreplace')
