import os
import random
import string
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login, authenticate
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import DetailView, View, ListView
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .forms import OrderForm, LoginForm, RegistrationForm
from .mixins import CartMixin
from .models import Category, SubCategory, Customer, OrderProduct, Product, Order
from .utils import recalc_order
import telepot

User = get_user_model()

group_id = -543527686
telegram_token = os.getenv('telegram_token')
telegramBot = telepot.Bot(telegram_token)  # token


def send_telegram(text):
    telegramBot.sendMessage(group_id, text, parse_mode="Markdown")


class MyQ(Q):
    default = 'OR'


class BaseView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        products = Product.objects.all()
        popular_products = Product.objects.all().order_by('-visits')[0:12]
        recently_viewed_products = Product.objects.all().order_by('-last_visit')[0:4]

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
        print(context)
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
        user = User.objects.filter(username=request.user).first()
        if user:
            customer.user = user
        customer.save()

        order, created = Order.objects.get_or_create(owner=customer, status='cart')
        self.order = order

        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        order_product, created = OrderProduct.objects.get_or_create(
            order=self.order, product=product
        )
        if created:
            self.order.products.add(order_product)
        recalc_order(self.order)
        messages.add_message(request, messages.INFO, "Товар успешно добавлен")

        response = HttpResponseRedirect('/cart/')
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
        recalc_order(self.order)
        messages.add_message(request, messages.INFO, "Товар удален из корзины")
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
            messages.add_message(request, messages.INFO, "Кол-во товара изменено")
        else:
            self.order.products.remove(order_product)
            order_product.delete()
            messages.add_message(request, messages.INFO, "Товар удален из корзины")
        order_product.save()
        recalc_order(self.order)
        return HttpResponseRedirect('/cart/')


class CartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        context = {
            'order': self.order,
            'categories': categories
        }
        return render(request, 'cart.html', context)


class CheckoutView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        form = OrderForm(request.POST or None)
        context = {
            'order': self.order,
            'categories': categories,
            'form': form
        }

        return render(request, 'checkout.html', context)


class MakeOrderView(CartMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        user = User.objects.get(username=request.user)
        session = request.COOKIES.get('customersession')
        print('user, session:', user.id, session)
        customer = Customer.objects.get(user=user.id, session=session)
        order = Order.objects.get(owner=customer, status='cart')

        if form.is_valid():
            new_order = form.save(commit=False)
            # order.owner = customer
            order.first_name = user.first_name
            order.last_name = user.last_name
            order.phone = customer.phone
            order.address = form.cleaned_data['address']
            order.buying_type = form.cleaned_data['buying_type']
            order.comment = form.cleaned_data['comment']
            order.status = 'new'
            order.save()

            # customer.orders.add(new_order)
            messages.add_message(request, messages.INFO, 'Спасибо за заказ! Менеджер с Вами свяжется')
            # send_telegram('Поступил новый заказ из интернет магазина. http://introvert.com.ru/admin/mainapp/order/')

            html = render_to_string('order_placed.html', {'user': user, 'order': order})
            send_mail('Заказ в магазине Интроверт', 'Спасибо за Ваш заказ в магазине Интроверт!',
                      'Интроверт<noreply@introvert.com.ru>', [user.email], fail_silently=False, html_message=html)

            response = HttpResponseRedirect('/profile/')
            new_session = get_random_session()
            response.set_cookie(key='customersession', value=new_session)
            return response

        return HttpResponseRedirect('/checkout/')


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
                session = request.COOKIES.get('customersession')
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
            new_user.first_name = form.cleaned_data['first_name']
            new_user.last_name = form.cleaned_data['last_name']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            user = authenticate(
                username=new_user.username, password=form.cleaned_data['password']
            )
            login(request, user)
            customer = Customer.objects.get(session=session)
            customer.user = user
            # new_user = form.save(commit=False)
            customer.phone = form.cleaned_data['phone']
            customer.address = form.cleaned_data['address']
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
        owner = Customer.objects.filter(user=request.user).first()
        orders = Order.objects.filter(~Q(status='cart'), owner=owner).order_by('-created_at')
        print(Order.objects.all())

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
