from cachemodel.models import CacheModel
from django.views.generic import DetailView

class CachedDetailView(DetailView):
    def get_object(self, *args, **kwargs):
        for arg in ('pk','slug'):
            value = self.kwargs.get(arg, None)
            if value is not None:
                return self.model.objects.get_cached(**{arg: value})

        raise AttributeError('Need either pk or slug')
