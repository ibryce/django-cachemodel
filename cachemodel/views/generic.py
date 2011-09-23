from cachemodel.models import CacheModel
from django.views.generic import DetailView

class CachedDetailView(DetailView):
    def get_object(self, **kwargs):
        if not isinstance(self.model, CacheModel):
            return super(CachedDetailView, self).get_object(**kwargs)
        pk = self.kwargs.get('pk', None)
        slug = self.kwargs.get('slug', None)
        if pk is not None:
            obj = self.model.objects.get_by_pk(pk)
        elif slug is not None:
            obj = self.model.objects.get_by_slug(slug)
        else:
            raise AttributeError('Need either pk or slug')
        return obj

