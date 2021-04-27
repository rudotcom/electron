from django.core.cache import cache
from django.views.generic import View

from .models import Order, Customer, Article


class CartMixin(View):

    def __init__(self):
        super().__init__()
        self.articles = cache.get_or_set('article_menu', Article.objects.all(), timeout=600)

    def dispatch(self, request, *args, **kwargs):

        try:
            session = request.COOKIES.get('customersession')
            customer = Customer.objects.get(session=session)
            self.order = Order.carts.get(owner=customer)

        except:
            self.order = None

        return super().dispatch(request, *args, **kwargs)


class RequiredFieldsMixin:

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        fields_required = getattr(self.Meta, 'fields_required', None)

        if fields_required:
            for key in self.fields:
                if key in fields_required:
                    self.fields[key].required = True
