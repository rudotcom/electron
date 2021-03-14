from django.views.generic import View

from .models import Order, Customer


class CartMixin(View):

    def dispatch(self, request, *args, **kwargs):

        try:
            session = request.COOKIES.get('customersession')
            customer = Customer.objects.get(session=session)
            self.order = Order.objects.get(owner=customer, status='cart')

        except:
            self.order = None

        return super().dispatch(request, *args, **kwargs)
