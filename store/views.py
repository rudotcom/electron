import os
import random
import string
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login, authenticate
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views.generic import DetailView, View, ListView
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .forms import LoginForm, RegistrationForm, CartForm, CourierOrderForm, CDEKOrderForm, \
    PostRuOrderForm, PostWorldOrderForm, PaymentMethodForm, SelfOrderForm
from .mixins import CartMixin
from .models import Category, SubCategory, Customer, OrderProduct, Product, Order, FREE_GIFT
import telepot

User = get_user_model()

group_id = -543527686
telegram_token = os.getenv('telegram_token')
telegramBot = telepot.Bot(telegram_token)  # token


def send_telegram(text):
    telegramBot.sendMessage(group_id, text, parse_mode="Markdown")


class MyQ(Q):
    default = 'OR'


class GiftListView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        gift_products = Product.objects.filter(gift=True)
        context = {
            'bonus_sum': FREE_GIFT,
            'categories': categories,
            'products': gift_products,
            'order': self.order
        }
        return render(request, 'gift_list.html', context)


class BaseView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        # products = Product.objects.all()
        popular_products = Product.objects.all().order_by('-visits')[0:12]
        # recently_viewed_products = Product.objects.all().order_by('-last_visit')[0:4]

        context = {
            'categories': categories,
            'products': popular_products,
            'order': self.order
        }
        return render(request, 'base.html', context)


class ProductDetailView(CartMixin, DetailView):

    model = Product
    context_object_name = 'product'
    template_name = 'product_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        product = self.get_object()
        product.visits += 1
        product.last_visit = datetime.now()
        product.save()

        context = super().get_context_data(**kwargs)
        context['categories'] = self.get_object().category.__class__.objects.all()
        context['order'] = self.order

        return context


class SubCategoryDetailView(CartMixin, DetailView):
    model = SubCategory
    queryset = SubCategory.objects.all()
    context_object_name = 'subcategory'
    template_name = 'subcategory_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subcategory = self.get_object()
        category = Category.objects.get(subcategory=subcategory)
        context['order'] = self.order
        context['category'] = category
        context['categories'] = Category.objects.all()
        context['category_name'] = category.name
        context['subcategories'] = self.model.objects.filter(category=category)
        context['subcategory_name'] = subcategory.name
        context['subcategory_products'] = subcategory.product_set.all()
        return context


class CategoryDetailView(CartMixin, DetailView):
    model = Category
    queryset = Category.objects.all()
    context_object_name = 'category'
    template_name = 'category_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        context['order'] = self.order
        context['categories'] = self.model.objects.all()
        context['category_name'] = category.name
        context['subcategories'] = SubCategory.objects.filter(category=category)
        context['category_products'] = category.product_set.all()
        return context


class ProductSearchView(CartMixin, ListView):
    model = Product
    template_name = 'product_search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        context['categories'] = Category.objects.all()
        return context

    def get_queryset(self):
        query = self.request.GET.get('p')
        object_list = Product.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
        return object_list


def get_random_session():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=36))


class AddToCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        session = request.COOKIES.get('customersession') or get_random_session()

        customer, created = Customer.objects.get_or_create(session=session)
        if request.user.is_authenticated:
            user = User.objects.get(username=request.user)
            customer.user = user
        customer.save()

        self.order, created = Order.objects.get_or_create(owner=customer, status='cart')
        if created:
            # Это создание новой корзины. Удалить корзины старше 2 дней
            old_carts = Order.objects.filter(status__exact='cart', created_at__lte=datetime.now() - timedelta(days=2))
            old_carts.delete()

        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        if product.gift and not self.order.gift and self.order.final_price >= FREE_GIFT:
            self.order.gift = product
            self.order.save()
            messages.add_message(request, messages.INFO, f'Подарок добавлен к Вашему заказу: {product}')
        else:
            order_product, created = OrderProduct.objects.get_or_create(
                order=self.order, product=product
            )

            if created:
                self.order.products.add(order_product)
            else:
                order_product.qty += 1
                order_product.save()
            self.order.save()
            messages.add_message(request, messages.INFO, f'Товар "{order_product}" добавлен в корзину')

        response = HttpResponseRedirect(f"/product/{product_slug}/")
        response.set_cookie(key='customersession', value=session)
        return response


class DeleteFromCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        order_product = OrderProduct.objects.get(
            order=self.order, product=product
        )

        self.order.products.remove(order_product)
        order_product.delete()
        self.order.save()
        messages.add_message(request, messages.INFO, f'Товар "{order_product}" удален из корзины')
        return HttpResponseRedirect('/cart/')


class ChangeQTYView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        order_product = OrderProduct.objects.get(
            order=self.order, product=product
        )
        qty = int(request.POST.get('qty'))

        if qty:
            order_product.qty = qty
            messages.add_message(request, messages.INFO, f'Количество товара "{order_product}" изменено')
            order_product.save()
        else:
            self.order.products.remove(order_product)
            order_product.delete()
            messages.add_message(request, messages.INFO, f'Товар "{order_product}" удален из корзины')
        self.order.save()
        return HttpResponseRedirect('/cart/')


class CartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        form = CartForm(request.POST or None)
        if self.order:
            self.order.delivery_type = 'self'
            self.order.save()

        context = {
            'bonus_sum': FREE_GIFT,
            'order': self.order,
            'categories': categories,
            'form': form,
        }
        return render(request, 'cart.html', context)


class CheckoutView(CartMixin, View):

    def post(self, request, *args, **kwargs):

        self.order.delivery_type = request.POST.get('delivery_type')
        self.order.save()

        categories = Category.objects.all()
        if self.order.delivery_type == 'self':
            form = SelfOrderForm()
        elif self.order.delivery_type == 'delivery_spb':
            form = CourierOrderForm()
        elif self.order.delivery_type == 'delivery_cdekspb':
            form = CDEKOrderForm()
        elif self.order.delivery_type == 'delivery_ru':
            form = PostRuOrderForm()
        elif self.order.delivery_type == 'delivery_world':
            form = PostWorldOrderForm()

        context = {
            'order': self.order,
            'categories': categories,
            'form': form,
        }

        return render(request, 'checkout.html', context)


class MakeOrderView(CartMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if self.order.delivery_type == 'self':
            form = SelfOrderForm(request.POST or None)
        elif self.order.delivery_type == 'delivery_spb':
            form = CourierOrderForm(request.POST or None)
        elif self.order.delivery_type == 'delivery_cdekspb':
            form = CDEKOrderForm(request.POST or None)
        elif self.order.delivery_type == 'delivery_ru':
            form = PostRuOrderForm(request.POST or None)
        elif self.order.delivery_type == 'delivery_world':
            form = PostWorldOrderForm(request.POST or None)

        user = User.objects.get(username=request.user)
        session = request.COOKIES.get('customersession')

        customer = Customer.objects.get(user=user.id, session=session)
        order = Order.objects.get(owner=customer, status='cart')

        if form.is_valid():
            if 'first_name' in form.cleaned_data.keys():
                order.first_name = form.cleaned_data['first_name']
            if 'last_name' in form.cleaned_data.keys():
                order.last_name = form.cleaned_data['last_name']
            if 'patronymic' in form.cleaned_data.keys():
                order.patronymic = form.cleaned_data['patronymic']
            if 'phone' in form.cleaned_data.keys():
                order.phone = form.cleaned_data['phone']
            if 'postal_code' in form.cleaned_data.keys():
                order.postal_code = form.cleaned_data['postal_code']
            if 'settlement' in form.cleaned_data.keys():
                order.settlement = form.cleaned_data['settlement']
            if 'address' in form.cleaned_data.keys():
                order.address = form.cleaned_data['address']
            if 'payment_type' in form.cleaned_data.keys():
                order.payment_type = form.cleaned_data['payment_type']
            if 'comment' in form.cleaned_data.keys():
                order.comment = form.cleaned_data['comment']

            order.status = 'new'
            order.save()

            messages.add_message(request, messages.INFO,
                                 'Спасибо за заказ! Уведомление о заказе Вы получите по электронной почте')

            teleg = 'Новый заказ introvert.com.ru\n'  # Текст для телеграма

            for item in order.products.all():
                teleg += f"- {item}, {item.qty} шт\n"
            if order.gift:
                teleg += f"- Подарок: {order.gift}\n"
            teleg += f"{order.final_price}\n"
            teleg += f"{dict(order.PAYMENT_CHOICES)[order.payment_type]}\n"
            teleg += f"{dict(order.DELIVERY_TYPE_CHOICES)[order.delivery_type]}\n"
            if order.delivery_type.startswith('delivery'):
                teleg += f"{order.address}\n{order.settlement} {order.postal_code}\n"

            # print(teleg)
            send_telegram(teleg)
            html = render_to_string('order_placed.html', {'user': user, 'order': order})
            send_mail('Заказ в магазине Интроверт', 'Спасибо за Ваш заказ в магазине Интроверт!',
                      'Интроверт<noreply@introvert.com.ru>', [user.email], fail_silently=False, html_message=html)

            response = HttpResponseRedirect(f'/order_pay/{order.id}/')
            new_session = get_random_session()
            response.set_cookie(key='customersession', value=new_session)
            return response

        return HttpResponseRedirect('/checkout/')


class PayView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login/')

        form = PaymentMethodForm(request.POST or None)
        order_id = kwargs.get('order')

        pay_order = Order.objects.get(id=order_id)

        categories = Category.objects.all()
        return render(
            request,
            'page_payment.html',
            {
                'form': form,
                'order': self.order,
                'pay_order': pay_order,
                'categories': categories,
            }
        )


class BankPayView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        order_id = request.POST.get('order')
        print(request.POST)
        return HttpResponse('<a href=/>Home</a><br>Форма платежной системы. Bank Payment. Order ' + str(order_id))


class LoginView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        categories = Category.objects.all()
        context = {
            'form': form,
            'categories': categories,
            'order': self.order
        }
        return render(request, 'login.html', context)

    def post(self, request, *args, **kwargs):

        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(
                username=username, password=password
            )
            if user:
                session = request.COOKIES.get('customersession') or get_random_session()
                customer, created = Customer.objects.get_or_create(session=session)

                customer.user = user
                customer.save()

                login(request, user)
                return HttpResponseRedirect('/cart/')
        categories = Category.objects.all()
        context = {
            'form': form,
            'order': self.order,
            'categories': categories
        }
        return render(request, 'login.html', context)


class RegistrationView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        categories = Category.objects.all()
        context = {
            'form': form,
            'categories': categories,
            'order': self.order
        }
        return render(request, 'registration.html', context)

    def post(self, request, *args, **kwargs):
        session = request.COOKIES.get('customersession')
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.email = form.cleaned_data['email']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            user = authenticate(
                username=new_user.username, password=form.cleaned_data['password']
            )
            login(request, user)
            session = request.COOKIES.get('customersession') or get_random_session()
            customer, created = Customer.objects.get_or_create(session=session)
            if user:
                customer.user = user
            customer.save()

            return HttpResponseRedirect('/cart/')
        categories = Category.objects.all()
        context = {
            'form': form,
            'categories': categories,
            'order': self.order
        }
        return render(request, 'registration.html', context)


class ProfileView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login/')

        owners = Customer.objects.filter(user=request.user)
        orders = Order.objects.filter(~Q(status='cart'), owner__in=owners).order_by('-created_at')

        categories = Category.objects.all()
        return render(
            request,
            'profile.html',
            {
                'orders': orders,
                'order': self.order,
                'categories': categories,
            }
        )


# class AboutView(CartMixin, View):
#
#     def get(self, request, *args, **kwargs):
#         categories = Category.objects.all()
#
#         context = {
#             'categories': categories,
#             'order': self.order
#         }
#         return render(request, 'flatpages/default.html', context)
