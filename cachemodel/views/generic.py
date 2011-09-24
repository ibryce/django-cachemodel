from cachemodel.models import CacheModel
from django.views.generic import DetailView

class CachedDetailView(DetailView):
    def get_object(self, *args, **kwargs):
        get_by_fun = getattr(self.model.objects, 'get_by', None)
        if not callable(get_by_fun):
            return super(CachedDetailView, self).get_object(*args, **kwargs)

        for arg in ('pk','slug'):
            value = self.kwargs.get(arg, None)
            if value is not None:
                return get_by_fun(arg, value)

        raise AttributeError('Need either pk or slug')
