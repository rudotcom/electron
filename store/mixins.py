import random
import string

from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin

from .models import Order, Customer, SubCategory


def get_random():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=36))


class CartMixin(View):

    def dispatch(self, request, *args, **kwargs):
        try:
            customer = Customer.objects.get(user=request.user)
            print(customer)
            if not self.order:
                self.order = Order.objects.get_or_create(owner=customer)
        except:
            try:
                session = request.session['session']
            except:
                session = get_random()
                request.session['session'] = session
            customer, created = Customer.objects.get_or_create(session=session)

        self.order = Order.objects.filter(owner=customer, status='cart').first()


        return super().dispatch(request, *args, **kwargs)


class SubCategoryDetailMixin(SingleObjectMixin):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subcategories'] = SubCategory.objects.get_subcategory_list()
        return context


